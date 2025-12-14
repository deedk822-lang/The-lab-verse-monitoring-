#!/usr/bin/env python3
"""
Comprehensive Model Setup Script
Downloads and configures all required AI models for Vaal AI Empire
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import requests
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelSetup:
    """Setup and download all required models"""

    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        self.cache_dir = Path.home() / ".cache" / "vaal-ai-empire"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed"""
        try:
            result = subprocess.run(
                ["ollama", "version"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"✅ Ollama installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass

        logger.warning("⚠️  Ollama not installed")
        return False

    def install_ollama(self):
        """Install Ollama (Linux/Mac)"""
        logger.info("Installing Ollama...")

        if sys.platform == "darwin" or sys.platform.startswith("linux"):
            try:
                subprocess.run(
                    ["curl", "-fsSL", "https://ollama.com/install.sh"],
                    stdout=subprocess.PIPE,
                    check=True
                )
                subprocess.run(["sh"], stdin=subprocess.PIPE, check=True)
                logger.info("✅ Ollama installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install Ollama: {e}")
                logger.info("Please install manually from https://ollama.com")
        else:
            logger.info("Windows detected. Please download Ollama from https://ollama.com/download")

    def download_ollama_model(self, model_name: str) -> bool:
        """Download a model via Ollama"""
        logger.info(f"Downloading {model_name} via Ollama...")

        try:
            # Pull the model
            result = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info(f"✅ {model_name} downloaded successfully")
                return True
            else:
                logger.error(f"❌ Failed to download {model_name}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Error downloading {model_name}: {e}")
            return False

    def setup_mistral_models(self):
        """Setup Mistral models via Ollama"""
        logger.info("\n=== Setting up Mistral Models ===")

        if not self.check_ollama_installed():
            self.install_ollama()
            if not self.check_ollama_installed():
                logger.error("Cannot proceed without Ollama. Please install manually.")
                return False

        # Download recommended Mistral models
        models = [
            "mistral:latest",           # Main text generation
            "mistral:7b-instruct",      # Instruction following
        ]

        for model in models:
            self.download_ollama_model(model)

        # Test Ollama connection
        try:
            import ollama
            response = ollama.chat(
                model="mistral:latest",
                messages=[{"role": "user", "content": "Hello"}]
            )
            logger.info("✅ Mistral models working correctly")
            return True
        except Exception as e:
            logger.error(f"❌ Mistral setup failed: {e}")
            return False

    def setup_huggingface_models(self):
        """Setup HuggingFace models for local inference"""
        logger.info("\n=== Setting up HuggingFace Models ===")

        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch

            # Use a smaller, efficient model for local inference
            model_name = "microsoft/phi-2"  # 2.7B parameter model, good quality

            logger.info(f"Downloading {model_name}...")

            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir)
            )

            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir),
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )

            logger.info("✅ HuggingFace model downloaded successfully")
            logger.info(f"   Model cached at: {self.cache_dir}")

            # Test inference
            inputs = tokenizer("Hello, I am", return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            outputs = model.generate(**inputs, max_length=20)
            result = tokenizer.decode(outputs[0])
            logger.info(f"   Test generation: {result}")

            return True

        except Exception as e:
            logger.error(f"❌ HuggingFace setup failed: {e}")
            logger.info("Installing required packages...")
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "transformers", "torch", "accelerate"
            ])
            return False

    def setup_sentence_transformers(self):
        """Setup sentence transformers for embeddings"""
        logger.info("\n=== Setting up Sentence Transformers ===")

        try:
            from sentence_transformers import SentenceTransformer

            # Download a good multilingual model
            model_name = "paraphrase-multilingual-mpnet-base-v2"
            logger.info(f"Downloading {model_name}...")

            model = SentenceTransformer(
                model_name,
                cache_folder=str(self.cache_dir)
            )

            # Test encoding
            embeddings = model.encode(["Test sentence", "Another test"])
            logger.info(f"✅ Sentence Transformers working (embedding dim: {embeddings.shape[1]})")

            return True

        except Exception as e:
            logger.error(f"❌ Sentence Transformers setup failed: {e}")
            return False

    def verify_api_keys(self) -> Dict[str, bool]:
        """Verify all API keys are set"""
        logger.info("\n=== Verifying API Keys ===")

        api_keys = {
            "COHERE_API_KEY": os.getenv("COHERE_API_KEY"),
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
            "HUGGINGFACE_TOKEN": os.getenv("HUGGINGFACE_TOKEN"),
            "AYRSHARE_API_KEY": os.getenv("AYRSHARE_API_KEY"),
            "MAILCHIMP_API_KEY": os.getenv("MAILCHIMP_API_KEY"),
            "ASANA_ACCESS_TOKEN": os.getenv("ASANA_ACCESS_TOKEN"),
        }

        results = {}
        for key, value in api_keys.items():
            if value and len(value) > 5:
                logger.info(f"✅ {key}: Set ({value[:10]}...)")
                results[key] = True
            else:
                logger.warning(f"⚠️  {key}: Not set or invalid")
                results[key] = False

        return results

    def test_cohere_api(self) -> bool:
        """Test Cohere API connection"""
        logger.info("\n=== Testing Cohere API ===")

        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            logger.warning("⚠️  COHERE_API_KEY not set")
            return False

        try:
            import cohere
            client = cohere.Client(api_key)

            # Test chat
            response = client.chat(
                model="command-r",
                message="Say hello",
                max_tokens=10
            )

            logger.info(f"✅ Cohere API working: {response.text[:50]}...")
            return True

        except Exception as e:
            logger.error(f"❌ Cohere API test failed: {e}")
            return False

    def test_groq_api(self) -> bool:
        """Test Groq API connection"""
        logger.info("\n=== Testing Groq API ===")

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning("⚠️  GROQ_API_KEY not set")
            return False

        try:
            from groq import Groq
            client = Groq(api_key=api_key)

            completion = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=10
            )

            logger.info(f"✅ Groq API working: {completion.choices[0].message.content}")
            return True

        except Exception as e:
            logger.error(f"❌ Groq API test failed: {e}")
            logger.info("Install groq: pip install groq")
            return False

    def create_model_config(self):
        """Create model configuration file"""
        logger.info("\n=== Creating Model Configuration ===")

        config = {
            "models": {
                "text_generation": {
                    "primary": {
                        "provider": "cohere",
                        "model": "command-r",
                        "fallback": "mistral:latest"
                    },
                    "local": {
                        "provider": "ollama",
                        "model": "mistral:latest",
                        "host": "http://localhost:11434"
                    },
                    "fast": {
                        "provider": "groq",
                        "model": "mixtral-8x7b-32768"
                    }
                },
                "embeddings": {
                    "primary": {
                        "provider": "cohere",
                        "model": "embed-english-v3.0"
                    },
                    "local": {
                        "provider": "sentence-transformers",
                        "model": "paraphrase-multilingual-mpnet-base-v2"
                    }
                },
                "chat": {
                    "primary": {
                        "provider": "cohere",
                        "model": "command-r"
                    }
                }
            },
            "costs": {
                "cohere": {
                    "command-r": {
                        "input": 0.00015,
                        "output": 0.00060
                    },
                    "embed-english-v3.0": {
                        "per_1k": 0.0001
                    }
                },
                "groq": {
                    "mixtral-8x7b-32768": {
                        "input": 0.00027,
                        "output": 0.00027
                    }
                }
            }
        }

        import json
        config_path = self.models_dir / "model_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"✅ Model config saved to {config_path}")

    def run_full_setup(self):
        """Run complete setup process"""
        logger.info("=" * 60)
        logger.info("VAAL AI EMPIRE - MODEL SETUP")
        logger.info("=" * 60)

        results = {
            "api_keys": False,
            "cohere": False,
            "groq": False,
            "mistral": False,
            "huggingface": False,
            "sentence_transformers": False
        }

        # Check API keys
        api_status = self.verify_api_keys()
        results["api_keys"] = any(api_status.values())

        # Test APIs
        results["cohere"] = self.test_cohere_api()
        results["groq"] = self.test_groq_api()

        # Setup local models
        results["mistral"] = self.setup_mistral_models()
        results["huggingface"] = self.setup_huggingface_models()
        results["sentence_transformers"] = self.setup_sentence_transformers()

        # Create config
        self.create_model_config()

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("SETUP SUMMARY")
        logger.info("=" * 60)

        for component, status in results.items():
            emoji = "✅" if status else "❌"
            logger.info(f"{emoji} {component.replace('_', ' ').title()}: {'OK' if status else 'Failed'}")

        if any(results.values()):
            logger.info("\n🎉 Setup completed! At least one model provider is available.")
            logger.info("\nNext steps:")
            logger.info("1. Start Ollama: ollama serve")
            logger.info("2. Set up environment variables in .env")
            logger.info("3. Run: python scripts/test_all.py")
        else:
            logger.error("\n❌ Setup failed! Please check errors above.")
            logger.info("\nRequired actions:")
            logger.info("1. Install Ollama from https://ollama.com")
            logger.info("2. Set API keys in .env file")
            logger.info("3. Install dependencies: pip install -r requirements.txt")


def main():
    """Main setup function"""
    setup = ModelSetup()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "mistral":
            setup.setup_mistral_models()
        elif command == "huggingface":
            setup.setup_huggingface_models()
        elif command == "embeddings":
            setup.setup_sentence_transformers()
        elif command == "verify":
            setup.verify_api_keys()
            setup.test_cohere_api()
            setup.test_groq_api()
        elif command == "config":
            setup.create_model_config()
        else:
            logger.info("Usage: python setup_models.py [mistral|huggingface|embeddings|verify|config]")
    else:
        # Run full setup
        setup.run_full_setup()


if __name__ == "__main__":
    main()