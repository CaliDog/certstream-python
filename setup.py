from setuptools import setup
import os

here = os.path.abspath(os.path.dirname(__file__))

with open('requirements.txt') as f:
    dependencies = f.read().splitlines()

long_description = """
Certstream is a library to connect to the certstream network (certstream.calidog.io). 

It supports automatic reconnection when networks issues occur, and should be stable for long-running jobs. 
"""

setup(
    name='certstream',
    version="1.9",
    url='https://github.com/CaliDog/certstream-python/',
    author='Ryan Sears',
    install_requires=dependencies,
    setup_requires=dependencies,
    author_email='ryan@calidog.io',
    description='CertStream is a library for receiving certificate transparency list updates in real time.',
    long_description=long_description,
    packages=['certstream',],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'certstream = certstream.cli:main',
        ],
    },
    license = "MIT",
    classifiers = [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security :: Cryptography",
        "Environment :: Console",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2",
        "Framework :: AsyncIO"
    ],
)
