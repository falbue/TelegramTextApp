from setuptools import setup, find_packages
import re

def get_version_from_file(file_path: str, version_var: str = "VERSION"):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = rf"^{version_var}\s*=\s*['\"](.*?)['\"]|{version_var}\s*=\s*([\d.]+)"
    match = re.search(pattern, content, re.MULTILINE)
    if match:
        return match.group(1) or match.group(2)
    return None

version = get_version_from_file("TelegramTextApp/handler.py")

setup(
    name='TelegramTextApp',
    version=version,
    packages=find_packages(where="."),
    include_package_data=True,
    package_data={
        "developer_application": ["*"],
    },
    install_requires=[
        'aiogram',
        'aiohttp',
        'aiosqlite',
        'asyncio',
        'dotenv',
        'requests'
    ],
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