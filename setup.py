 feature/elite-ci-cd-pipeline-1070897568806221897
import setuptools

setuptools.setup()

from setuptools import setup, find_packages

setup(
    name="rainmaker-orchestrator",
    version="0.1.0",
    description="AI-powered task orchestration and self-healing system",
    author="Your Name",
    author_email="your.email@example.com",

    # SRC-LAYOUT CONFIGURATION
    package_dir={"": "src"},
    packages=find_packages(where="src"),

    python_requires=">=3.10",

    install_requires=[
        "fastapi>=0.109.2",
        "uvicorn[standard]>=0.27.1",
        "pydantic>=2.6.1",
        "pydantic-settings>=2.1.0",
        "openai>=1.12.0",
        "redis[hiredis]>=5.2.1",
        "httpx>=0.26.0",
        "prometheus-client>=0.19.0",
        "PyYAML>=6.0.1",
        "python-dotenv>=1.0.1",
    ],

    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.1.0",
            "black>=24.3.0",
            "mypy>=1.8.0",
        ]
    },

    entry_points={
        "console_scripts": [
            "rainmaker=rainmaker_orchestrator.cli:main",
        ],
    },

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
