from setuptools import setup, find_packages

setup(
    name="vaal-ai-empire",
    version="1.0.0",
    description="Vaal AI Empire - Authority Engine with Tax & Content Agents",
    author="deedk822-lang",
    packages=find_packages(where="src"),
    package_dir={"":" src"},
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn>=0.32.0",
        "huggingface_hub>=0.26.0",
        "requests>=2.32.0",
        "mcp>=1.1.2",
        "databricks-sdk>=0.38.0",
        "httpx>=0.28.0",
        "dashscope>=1.20.0",
        "openai>=1.54.0",
        "cohere>=5.11.0",
        "mistralai>=1.2.0",
        "groq>=0.11.0",
        "oss2>=2.18.0",
        "pandas>=2.2.0",
    ],
)
