from setuptools import setup, find_packages

setup(
    name='TelegramTextApp',
    version='0.5.1.6',
    packages=find_packages(),
    package_data={
        "developer_application": ["*"],  # Включить все файлы в app/templates
    },
    install_requires=[
        'telebot',
        'pytz',
        'flask'
    ],
    description='Библиотека для создания текстовых приложений в telegram',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='falbue',
    author_email='cyansair05@gmail.com',
    url='https://github.com/falpin/TTA',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)