from setuptools import setup, find_packages

setup(
    name="pr-fix-agent",
    version="1.0.0",
    author="PR Fix Agent Team",
    description="AI-powered PR error fixing with Ollama",
    python_requires=">=3.8",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "requests>=2.28.0",
        "pytest>=7.0.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "ruff>=0.0.250",
            "mypy>=0.990",
        ],
    },
    entry_points={
        "console_scripts": [
            "pr-fix-agent=pr_fix_agent.production:main",
        ],
    },
)
