from setuptools import setup, find_packages
from pip._internal.network.session import PipSession
from pip._internal.req import parse_requirements

install_requires = [str(requirement.requirement) for requirement in parse_requirements('requirements.txt', session=PipSession())]

setup(
    name='smc360',
    version='1.0.0',
    packages=find_packages(),
    install_requires=install_requires,
    include_package_data=True,
    author='Mohammed Adil Farooq',
    author_email='adil.farooq@blend360.com',
    description='Social media parser for analyzing and exploring social media data.',
    long_description="""
        This program extracts data from social media platforms and stores parsed data in a database and raw response in object storage.
        The program will use the configuration data to connect to the social media platform, database, and object storage service. It will
        then load additional configuration data from the object storage service, parse the social media data, and store it in the database.

        The program supports the following services:
        - `Platform: YouTube(Youtube Data API), Instagram(Basic Display API)`
        - `Database: PostgreSQL, Snowflake`
        - `Object Storage: s3`

        Run: `smc360 -h` to get started.
    """,
    url='https://github.com/BLEND360/COE_Socialmedia_Parser',
    entry_points={
        'console_scripts': [
            'smc360 = smc360.cli:main'
        ]
    },
    python_requires='>=3.9'
)
