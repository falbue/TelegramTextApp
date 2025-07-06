from setuptools import setup, find_packages

# Чтение зависимостей из requirements.txt
with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name='TelegramTextApp',
    version='0.6.0',
    packages=find_packages(where="."),
    include_package_data=True,
    package_data={
        "developer_application": ["*"],
    },
    install_requires=install_requires,  # Используем зависимости из файла
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