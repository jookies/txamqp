import os
from setuptools import setup, find_packages


def parse_requirements(filename):
    """load requirements from a pip requirements file"""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and (not line.startswith("#") and not line.startswith('-'))]


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="txAMQP3",
    version='0.9.0',
    author="Esteve Fernandez",
    author_email="esteve@apache.org",
    description="Python3 library for communicating with AMQP peers and brokers using Twisted",
    license='Apache License 2.0',
    packages=find_packages(exclude=["tests"]),
    # long_description=read('README.md'),
    keywords="twisted amq",
    url="https://github.com/jookies/txamqp",
    py_modules=["txAMQP3"],
    include_package_data=True,
    package_data={'txamqp3': ['README.md']},
    install_requires=parse_requirements('requirements.txt'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Twisted",
        "Topic :: System :: Networking",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
