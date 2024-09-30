from setuptools import setup, find_packages

setup(
    name='ai_utilities',
    version='0.2.0',
    packages=find_packages(),
    install_requires=[
        'openai',
        'config_utilities',
        'psutil',
    ],
    description='Utilities for AI configuration management and integration.',
    author='Steffen S. Rasmussen',
    author_email='steffen@audkus.dk',
    url='https://github.com/audkus/ai_utilities.git'
)