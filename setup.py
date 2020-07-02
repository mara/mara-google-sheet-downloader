from setuptools import setup, find_packages
import re


def get_long_description():
    with open('README.md') as f:
        return re.sub('!\[(.*?)\]\(docs/(.*?)\)',
                      r'![\1](https://github.com/mara/mara-google-sheet-downloader/raw/master/docs/\2)', f.read())


setup(
    name='mara-google-sheet-downloader',
    version='1.0.0',

    description='Opinionated lightweight ETL pipeline framework',

    long_description=get_long_description(),
    long_description_content_type='text/markdown',

    url='https://github.com/mara/mara-google-sheet-downloader',

    install_requires=[
        'mara-db>=4.2.0',
        'mara-pipelines>=3.0.0',
        'gspread>=3.1.0',
        'oauth2client>=1.5.0', # old, will be replaced soon
        'google_auth_oauthlib' # new, already used in the user credential helper
    ],
    tests_require=['pytest'],

    python_requires='>=3.6',

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={},
)
