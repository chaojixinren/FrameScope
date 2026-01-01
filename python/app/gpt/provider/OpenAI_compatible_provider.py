from typing import Optional, Union

from openai import OpenAI

from app.utils.logger import get_logger

logging= get_logger(__name__)
class OpenAICompatibleProvider:
    def __init__(self, api_key: str, base_url: str, model: Union[str, None]=None):
        # 验证 API Key
        if not api_key or api_key.strip() == "":
            raise ValueError(f"API Key 不能为空。base_url: {base_url}")
        
        # 检查是否是占位符
        placeholder_keys = ['your_api_key_here', 'your_deepseek_api_key_here', 
                           'your_qwen_api_key_here', 'your_openai_api_key_here']
        if api_key.lower() in placeholder_keys:
            raise ValueError(f"API Key 是占位符，请替换为真实的 API Key。base_url: {base_url}")
        
        self.client = OpenAI(api_key=api_key.strip(), base_url=base_url)
        self.model = model

    @property
    def get_client(self):
        return self.client

    @staticmethod
    def test_connection(api_key: str, base_url: str) -> bool:
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            model = client.models.list()
            # for segment in model:
            #     print(segment)
            # print(model)
            logging.info("连通性测试成功")
            return True
        except Exception as e:
            logging.info(f"连通性测试失败：{e}")

            # print(f"Error connecting to OpenAI API: {e}")
            return False