from setuptools import setup, find_packages
import re

def parse_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

try:
    with open('version.py', 'r') as f:
        version_content = f.read()
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_content, re.M)
        if version_match:
            version = version_match.group(1)
        else:
            raise RuntimeError("Не удалось найти версию в version.py")
except FileNotFoundError:
    version = "0.0.1.dev0"

setup(
    name='TelegramTextApp',
    version=version,
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