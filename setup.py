import subprocess
import os

from setuptools import find_packages, setup

version='0.1'

if os.path.exists('VERSION'):
    try:
        with open('VERSION', 'r') as version_file:
            version = version_file.read().strip()
    except Exception as e:
        print(f'Failed to read version from VERSION file: {e}')


setup(
    name='openagents_node_sdk',
    packages=find_packages(),
    version=version,
    description='A Python SDK for OpenAgents Nodes',
    author='OpenAgents',
    setup_requires=['pytest-runner'],
    tests_require=['pytest==8.2.0'],
    install_requires=[
        "openagents-grpc-proto",
        "packaging",
        "requests"
    ]
)