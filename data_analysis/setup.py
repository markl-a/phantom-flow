"""
Data Analysis with Chatbots
A comprehensive framework for customer analytics using AI-powered chatbots
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="data-analysis-chatbots",
    version="1.0.0",
    author="賴祺清",
    author_email="",
    description="Customer analytics and segmentation using AI chatbots (ChatGPT, Gemini, Claude)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/markl-a/Data-Analysis-with-Chatbots",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.24.0,<2.0",
        "pandas>=2.0.0,<3.0",
        "scipy>=1.10.0,<2.0",
        "scikit-learn>=1.3.0,<2.0",
        "matplotlib>=3.7.0,<4.0",
        "seaborn>=0.12.0,<1.0",
        "plotly>=5.14.0,<6.0",
        "streamlit>=1.28.0,<2.0",
        "nltk>=3.8.0,<4.0",
        # Required by DataLoader.load_excel + pandas.to_excel; without it
        # CI fails with "ModuleNotFoundError: No module named 'openpyxl'"
        # at the Excel-IO test sites.
        "openpyxl>=3.1.0,<4.0",
        "pyyaml>=6.0.0,<7.0",
        "python-dotenv>=1.0.0,<2.0",
        "loguru>=0.7.0,<1.0",
        "tqdm>=4.66.0,<5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0,<8.0",
            "pytest-cov>=4.1.0,<5.0",
            "pytest-xdist>=3.3.0,<4.0",
            "black>=23.7.0,<25.0",
            "flake8>=6.1.0,<7.0",
            "isort>=5.12.0,<6.0",
            "mypy>=1.8.0,<2.0",
            "pylint>=3.0.0,<4.0",
            "bandit>=1.7.0,<2.0",
            "pre-commit>=3.6.0,<4.0",
        ],
        "notebooks": [
            "jupyter>=1.0.0,<2.0",
            "ipykernel>=6.25.0,<7.0",
            "ipywidgets>=8.1.0,<9.0",
        ],
        "kaggle": [
            "kaggle>=1.5.16,<2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dac-download=data_analysis_chatbots.cli:download_data",
            "dac-analyze=data_analysis_chatbots.cli:analyze",
        ],
    },
    include_package_data=True,
    package_data={
        "data_analysis_chatbots": ["config/*.yaml"],
    },
    project_urls={
        "Documentation": "https://github.com/markl-a/Data-Analysis-with-Chatbots/blob/main/README.md",
        "Source": "https://github.com/markl-a/Data-Analysis-with-Chatbots",
        "Issues": "https://github.com/markl-a/Data-Analysis-with-Chatbots/issues",
    },
    keywords=[
        "data-analysis",
        "customer-segmentation",
        "rfm-analysis",
        "chatgpt",
        "ai",
        "machine-learning",
        "clustering",
        "marketing-analytics",
    ],
)
