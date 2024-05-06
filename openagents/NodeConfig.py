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
            "about": "An new OpenAgents Node",
            "version": "0.0.1",
        }
        if meta:
            for k,v in meta.items():
                self._meta[k]=v

    def getMeta(self):
        self._meta["name"] = os.getenv('NODE_NAME', self._meta["name"])
        self._meta["description"] = os.getenv('NODE_DESCRIPTION', self._meta["description"])
        self._meta["about"] = os.getenv('NODE_DESCRIPTION', self._meta["about"])
        self._meta["description"] = os.getenv('NODE_DESCRIPTION', self._meta["description"])
        self._meta["version"] = os.getenv('NODE_VERSION', self._meta["version"])

        return self._meta

    def name(self,name:str)->'NodeConfig':
        """
        Set the name of the node.
        Args:
            name (str): The name of the node.
        Returns:
            NodeConfig: The node configuration.
        """
        self._meta["name"]=name
        return self

    def description(self,description:str)->'NodeConfig':
        """
        Set the description of the node.
        Args:
            description (str): The description of the node.
        Returns:
            NodeConfig: The node configuration.
        """
        self._meta["about"]=description
        self._meta["description"]=description
        return self

    def version(self,version:str)->'NodeConfig':
        """
        Set the version of the node.
        Args:
            version (str): The version of the node.
        Returns:
            NodeConfig: The node configuration.
        """
        self._meta["version"]=version
        return self
    