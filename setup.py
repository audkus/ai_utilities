from setuptools import setup, find_packages

setup(
    name='ai_utilities_audkus',
    version='0.2.0',
    packages=find_packages(),
    install_requires=[
        'openai',
        'config_utilities @ git+https://github.com/audkus/config_utilities.git',
        'psutil',
    ],
    description='Utilities for AI configuration management and integration.',
    author='Steffen S. Rasmussen',
    author_email='steffen@audkus.dk',
    url='https://github.com/audkus/ai_utilities.git'
)