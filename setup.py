import subprocess
import os

from setuptools import find_packages, setup

tag=None
try:
    tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0'], stderr=subprocess.DEVNULL).decode().strip()
except subprocess.CalledProcessError:
    tag = ""

if tag:
    tag = tag.lstrip('v')
else:
    tag = "0.1"



setup(
    name='openagents',
    packages=find_packages(),
    version=tag,
    description='A Python SDK for OpenAgents Nodes',
    author='OpenAgentsInc',
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    install_requires=[
        "grpcio==1.62.1",
        "protobuf==5.26.1",
        "packaging",
        "requests"
    ],
    dependency_links=[
        "https://github.com/OpenAgentsInc/openagents-grpc-proto/releases/download/v0.7.6/openagents_grpc_proto-PYTHON.tar.gz"
    ]
)