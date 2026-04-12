"""Setup configuration for GridNav OpenEnv environment."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="gridnav-openenv",
    version="1.0.0",
    author="OpenEnv Contributors",
    description="GridNav - A grid-based navigation environment following the OpenEnv specification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://huggingface.co/spaces/SurajSeth/openenv-scale",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.4.2",
            "pytest-cov>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "test": [
            "pytest>=8.4.2",
            "pytest-cov>=7.0.0",
        ],
    },
    python_requires=">=3.8",
    packages=find_packages(),
    package_data={
        "": ["*.yaml", "*.yml", "*.md"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords=[
        "openenv",
        "reinforcement-learning",
        "gridworld",
        "navigation",
        "item-collection",
        "ai-agents",
    ],
)
