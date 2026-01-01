from abc import ABC
import os

from app.decorators.timeit import timeit
from app.decorators.retry_rate_limit import retry_on_rate_limit
from app.models.transcriber_model import TranscriptResult, TranscriptSegment
from app.services.provider import ProviderService
from app.transcriber.base import Transcriber
from openai import OpenAI
import ffmpeg
import tempfile
from dotenv import load_dotenv
load_dotenv()
MAX_SIZE_MB = 18
MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024
def compress_audio(input_path: str, target_bitrate='64k') -> str:
    output_fd, output_path = tempfile.mkstemp(suffix=".mp3")  # 临时输出文件
    os.close(output_fd)  # 关闭文件描述符，ffmpeg 会用路径操作
    ffmpeg.input(input_path).output(output_path, audio_bitrate=target_bitrate).run(quiet=True, overwrite_output=True)
    return output_path

class GroqTranscriber(Transcriber, ABC):


    @timeit
    @retry_on_rate_limit(max_retries=3, base_delay=60)
    def transcript(self, file_path: str) -> TranscriptResult:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_SIZE_BYTES:
            print(f"文件超过 {MAX_SIZE_MB}MB，开始压缩（当前 {round(file_size / (1024 * 1024), 2)}MB）...")
            file_path = compress_audio(file_path)
            print(f"压缩完成，临时路径：{file_path}")
        provider = ProviderService.get_provider_by_id('groq')


        if not provider:
            raise Exception("Groq 供应商未配置,请配置以后使用。")
        
        api_key = provider.get('api_key')
        base_url = provider.get('base_url')
        
        # 验证 API Key 是否存在
        if not api_key or api_key.strip() == '':
            raise Exception("Groq API Key 为空，请检查数据库配置")
        
        # 确保 API Key 不包含 "Bearer " 前缀（OpenAI SDK 会自动添加）
        api_key = api_key.strip()
        if api_key.startswith('Bearer '):
            api_key = api_key[7:].strip()
            print(f"[Groq] 警告: API Key 包含 'Bearer ' 前缀，已自动移除")
        
        # 调试信息：验证配置（不打印完整 API Key）
        print(f"[Groq] Base URL: {base_url}")
        print(f"[Groq] API Key 已配置 (长度: {len(api_key)} 字符, 前缀: {api_key[:10]}...)")
        print(f"[Groq] 注意: OpenAI SDK 会自动在请求头中添加 'Authorization: Bearer {api_key[:10]}...'")
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        filename = file_path

        # 获取 Groq 转录模型，默认为 whisper-large-v3
        groq_model = os.getenv('GROQ_TRANSCRIBER_MODEL', 'whisper-large-v3')
        
        # 读取文件内容（在重试循环外读取，避免重复读取）
        with open(filename, "rb") as file:
            file_content = file.read()
        
        # 调用 API（如果遇到速率限制，装饰器会自动重试）
        transcription = client.audio.transcriptions.create(
            file=(filename, file_content),
            model=groq_model,
            response_format="verbose_json",
        )
        print(transcription.text)
        print(transcription)
        segments = []
        full_text = ""

        for seg in transcription.segments:
            text = seg.text.strip()
            full_text += text + " "
            segments.append(TranscriptSegment(
                start=seg.start,
                end=seg.end,
                text=text
            ))

        result = TranscriptResult(
            language=transcription.language,
            full_text=full_text.strip(),
            segments=segments,
            raw=transcription.to_dict()
        )
        return result
