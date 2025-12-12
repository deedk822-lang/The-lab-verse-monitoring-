import os
import logging
import httpx
from openai import OpenAI

logger = logging.getLogger("UniversalGateway")

class ModelGateway:
    def __init__(self):
        # 1. LOCAL SOVEREIGN NODE (Default)
        self.local_client = OpenAI(base_url="http://localhost:8080/v1", api_key="sk-local")

        # 2. CLOUD BACKUP (Alibaba/DeepSeek)
        self.cloud_key = os.getenv("DASHSCOPE_API_KEY")
        self.cloud_client = OpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=self.cloud_key
        ) if self.cloud_key else None

    def generate(self, prompt, model="gpt-4", force_cloud=False):
        """
        Smart Routing:
        - If 'force_cloud' is False, use LocalAI (Free).
        - If LocalAI fails, fallback to Cloud (Paid).
        """
        if not force_cloud:
            try:
                logger.info(f"🖥️  LOCAL EXECUTION ({model})...")
                return self.local_client.chat.completions.create(
                    model=model, # LocalAI maps 'gpt-4' to its internal model
                    messages=[{"role": "user", "content": prompt}]
                ).choices[0].message.content
            except Exception as e:
                logger.warning(f"⚠️  Local Node Offline: {e}. Switching to Cloud...")

        # Cloud Fallback
        if self.cloud_client:
            logger.info("☁️  CLOUD EXECUTION (Qwen)...")
            return self.cloud_client.chat.completions.create(
                model="qwen-max",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content

        return "❌ ALL SYSTEMS DOWN."
