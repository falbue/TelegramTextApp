import os
import re
from setuptools import setup, find_packages

def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "version.py")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            content = f.read()
            match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
            if match:
                return match.group(1)
    return "development"

def parse_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='TelegramTextApp',
    version=get_version(),
    packages=find_packages(where="."),
    include_package_data=True,
    package_data={
        "developer_application": ["*"],
    },
    install_requires=parse_requirements('requirements.txt'),
    description='Библиотека для создания текстовых приложений в telegram',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='falbue',
    author_email='cyansair05@gmail.com',
    url='https://github.com/falbue/TelegramTextApp',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)