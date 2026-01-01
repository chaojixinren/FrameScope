import os
import time
import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

load_dotenv()

# 默认 SQLite，如果想换 PostgreSQL 或 MySQL，可以直接改 .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///framescope.db")

# SQLite 需要特定连接参数，其他数据库不需要
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite 连接参数
    engine_args["connect_args"] = {
        "check_same_thread": False,  # 允许多线程访问
        "timeout": 30.0  # 30秒超时
    }
    # SQLite 连接池配置
    engine_args["pool_pre_ping"] = True  # 连接前检查连接是否有效
    engine_args["pool_size"] = 5  # 限制连接池大小
    engine_args["max_overflow"] = 10  # 最大溢出连接数

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
    **engine_args
)

# 为 SQLite 启用 WAL 模式（Write-Ahead Logging）以提高并发性能
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """为 SQLite 连接启用 WAL 模式，带重试机制"""
        cursor = dbapi_conn.cursor()
        max_retries = 3
        retry_delay = 0.1  # 100ms
        
        for attempt in range(max_retries):
            try:
                # 先设置 busy_timeout，这样如果数据库被锁定，会等待而不是立即失败
                cursor.execute("PRAGMA busy_timeout=30000")  # 30秒忙等待超时
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()
                return
            except (sqlite3.OperationalError, OperationalError) as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 递增延迟
                    continue
                else:
                    cursor.close()
                    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_engine():
    return engine


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()