import os
import subprocess

class SAAutoGLMAgent:
    def __init__(self):
        self.setup_sa_environment()

    def setup_sa_environment(self):
        """Setup optimized for South African conditions"""
        print("🇿🇦 Setting up AutoGLM for South Africa...")

        # Check internet connectivity
        self.internet_available = self.check_internet()

        # Check local resources
        self.local_model = self.check_local_model()

        # Setup appropriate configuration
        self.config = self.get_optimal_config()

        print(f"✅ Configuration: {self.config['mode']}")

    def check_internet(self):
        """Check if internet is available"""
        try:
            subprocess.run(["ping", "-c", "1", "8.8.8.8"],
                       timeout=5, check=True, capture_output=True)
            return True
        except:
            return False

    def check_local_model(self):
        """Check if local model is available"""
        return os.path.exists("models/autoglm-phone-9b-multilingual")

    def get_optimal_config(self):
        """Get the best configuration for current conditions"""
        if self.local_model:
            return {
                "mode": "local",
                "base_url": "http://localhost:8000/v1",
                "model": "autoglm-phone-9b-multilingual",
                "apikey": "",
                "max_steps": 50,
                "timeout": 30
            }
        elif self.internet_available:
            return {
                "mode": "cloud",
                "base_url": "https://api.z.ai/api/paas/v4",
                "model": "autoglm-phone-multilingual",
                "apikey": "your-api-key",
                "max_steps": 100,
                "timeout": 60
            }
        else:
            return {
                "mode": "offline",
                "base_url": None,
                "model": None,
                "apikey": None,
                "max_steps": 0,
                "timeout": 0
            }

    def run_autoglm(self, command):
        """Run AutoGLM with optimal configuration"""
        if self.config['mode'] == 'offline':
            return "❌ No internet or local model available"

        cmd = [
            "python3", "main.py",
            "--base-url", self.config['base_url'],
            "--model", self.config['model'],
            "--max-steps", str(self.config['max_steps']),
            "--timeout", str(self.config['timeout'])
        ]

        if self.config['apikey']:
            cmd.extend(["--apikey", self.config['apikey']])
        cmd.append(command)

        return subprocess.run(cmd, capture_output=True, text=True)

# Usage
agent = SAAutoGLMAgent()
result = agent.run_autoglm("Open Chrome and search for local news")
print(result.stdout)
