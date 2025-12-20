from setuptools import setup, find_packages

setup(
    name="vaal-ai-empire",
    version="1.0.0",
    description="Vaal AI Empire - Authority Engine with Tax & Content Agents",
    author="deedk822-lang",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "fastapi==0.111.0",
        "uvicorn==0.29.0",
        "huggingface_hub==0.23.0",
        "requests==2.32.3",
        "mcp==1.1.2",
        "databricks-sdk==0.20.0",
        "httpx==0.27.0",
        "dashscope==1.19.1",
        "openai==1.28.0",
        "cohere==5.4.0",
        "mistralai==0.1.5",
        "groq==0.5.0",
        "oss2==2.18.4",
        "pandas==2.2.2",
    ],
)
