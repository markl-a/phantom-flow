"""setup.py — minimal packaging for `pip install -e .` developer flow.

Most modern Python projects use pyproject.toml only, but a setup.py
shim is still the broadest-compatibility way to expose console scripts
on Windows + macOS + Linux without forcing the user to know which
build backend is in fashion this month. requirements.txt remains the
source of truth for runtime deps; setup.py mirrors the bare minimum.

After `pip install -e .`:
    automation-demo                # runs demo.py from anywhere
    python -c "import ai_automation_framework; ..."
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-automation-framework",
    version="0.5.0",
    description="Applied automation + AIOps + MLOps tools, built on phantom-mesh runtime",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="markl-a",
    url="https://github.com/markl-a/Automation_with_Agent",
    license="MIT",
    python_requires=">=3.10,<3.13",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
    install_requires=[
        # Heavy deps live in requirements.txt; this list is just what `import
        # ai_automation_framework` needs to not crash. Demo.py uses optional
        # imports so it works without anthropic/openai installed.
        "pydantic>=2.0",
        "python-dotenv>=1.0",
        "requests>=2.31",
    ],
    extras_require={
        "llm":  ["openai>=1.50,<2.0", "anthropic>=0.39,<1.0"],
        "rag":  ["langchain>=0.3,<1.0", "tiktoken>=0.7"],
        "dev":  ["pytest>=8.0", "pytest-cov", "black", "ruff", "mypy"],
        "all":  ["openai>=1.50,<2.0", "anthropic>=0.39,<1.0",
                 "langchain>=0.3,<1.0", "tiktoken>=0.7"],
    },
    entry_points={
        "console_scripts": [
            "automation-demo = demo:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
