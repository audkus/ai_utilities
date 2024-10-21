from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='ai_utilities',
    version='0.3.0',
    packages=find_packages(),
    install_requires=[
        'openai',
        'config_utilities',
        'psutil',
    ],
    description='Utilities for AI configuration management and integration.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Steffen S. Rasmussen',
    author_email='steffen@audkus.dk',
    url='https://github.com/audkus/ai_utilities.git'
)