from setuptools import setup, find_packages
import re

def get_long_description():
    with open('README.md') as f:
        return re.sub('!\[(.*?)\]\(docs/(.*?)\)', r'![\1](https://github.com/mara/mara-google-sheet-downloader/raw/master/docs/\2)', f.read())

setup(
    name='mara-google-sheet-downloader',
    version='2.7.0',

    description='Opinionated lightweight ETL pipeline framework',

    long_description=get_long_description(),
    long_description_content_type='text/markdown',

    url = 'https://github.com/mara/mara-google-sheet-downloader',

    install_requires=[
        'mara-db>=4.2.0',
        'data-integration>=2.7.0'
    ],

    python_requires='>=3.6',

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={},
)

