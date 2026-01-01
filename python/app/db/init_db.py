from app.db.models.models import Model
from app.db.models.providers import Provider
from app.db.models.video_tasks import VideoTask
from app.db.models.user import User
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.engine import get_engine, Base

def init_db():
    engine = get_engine()

    Base.metadata.create_all(bind=engine)