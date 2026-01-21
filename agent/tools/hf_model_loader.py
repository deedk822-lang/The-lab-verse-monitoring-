from __future__ import annotations

import logging
import os
from typing import Dict

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from agent.config import config

logger = logging.getLogger(__name__)


class HuggingFaceModelLoader:
    """Manages local Hugging Face model loading and inference."""

    def __init__(self) -> None:
        self.models: Dict[str, object] = {}
        self.tokenizers: Dict[str, object] = {}
        self.pipelines: Dict[str, object] = {}

        os.makedirs(config.hf.hf_cache_dir, exist_ok=True)
        logger.info("✅ HF model cache initialized: %s", config.hf.hf_cache_dir)

    async def load_model(self, model_id: str, task: str) -> object:
        if task in self.pipelines:
            logger.info("♻️ Using cached pipeline for %s", task)
            return self.pipelines[task]

        logger.info("📥 Loading model: %s", model_id)

        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            cache_dir=config.hf.hf_cache_dir,
            trust_remote_code=True,
            token=config.hf.hf_token,
        )

        kwargs = {
            "cache_dir": config.hf.hf_cache_dir,
            "device_map": "auto",
            "trust_remote_code": True,
        }

        if config.hf.load_in_8bit:
            kwargs["load_in_8bit"] = True
            logger.info("   Using 8-bit quantization")

        if config.hf.load_in_4bit:
            kwargs["load_in_4bit"] = True
            logger.info("   Using 4-bit quantization")

        model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=0 if config.hf.device == "cuda" else -1,
            max_new_tokens=config.hf.max_tokens,
            temperature=config.hf.temperature,
            top_p=config.hf.top_p,
            do_sample=True,
        )

        self.pipelines[task] = pipe
        self.models[task] = model
        self.tokenizers[task] = tokenizer

        logger.info("✅ Model loaded successfully: %s (%s)", model_id, task)
        return pipe

    async def inference(self, model_task: str, prompt: str, max_tokens: int = 1024) -> str:
        pipe = self.pipelines.get(model_task)
        if not pipe:
            raise ValueError(f"Pipeline not loaded for {model_task}")

        output = pipe(
            prompt,
            max_new_tokens=max_tokens,
            temperature=config.hf.temperature,
            top_p=config.hf.top_p,
        )
        return output[0]["generated_text"]

    def unload_model(self, task: str) -> None:
        if task in self.models:
            del self.models[task]
            del self.pipelines[task]
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("🧹 Unloaded model for task: %s", task)

    async def get_system_info(self) -> dict:
        return {
            "device": config.hf.device,
            "cuda_available": torch.cuda.is_available(),
            "models_loaded": list(self.pipelines.keys()),
            "cache_dir": config.hf.hf_cache_dir,
            "quantization": {"8bit": config.hf.load_in_8bit, "4bit": config.hf.load_in_4bit},
        }


model_loader = HuggingFaceModelLoader()
