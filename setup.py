from setuptools import setup, find_packages

setup(
    name="tiktok-save",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4",
        "requests",
        "selenium",
    ],
    python_requires=">=3.6",
) 