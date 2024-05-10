import os

class NodeConfig :
    """
    The configuration of an OpenAgents Node.
    Can be configured also with environment variables:
    - NODE_NAME: The name of the node.
    - NODE_DESCRIPTION: The description of the node.
    - NODE_VERSION: The version of the node.
    """
    def __init__(self, meta:dict=None):
        self._meta={
            "name": "OpenAgents Node",
            "description": "An new OpenAgents Node",
            "version": "0.0.1",
            "picture":""
        }
        if meta:
            for k,v in meta.items():
                self._meta[k]=v

    def getMeta(self):
        self._meta["name"] = os.getenv('NODE_NAME', self._meta["name"])
        self._meta["description"] = os.getenv('NODE_DESCRIPTION', self._meta["description"])
        self._meta["version"] = os.getenv('NODE_VERSION', self._meta["version"])
        return self._meta
