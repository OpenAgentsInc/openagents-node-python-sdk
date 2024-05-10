



class RunnerConfig:
    """
    A class to build an event (meta, template, socket schema, filter).
    """
    def __init__(self, meta:dict=None, filter:dict=None, template:str=None, sockets:dict=None):
        self._meta={
            "kind": 5003,
            "name": "An event template",
            "description": "",
            "tos": "",
            "privacy": "",
            "author": "",
            "web": "",
            "picture": "",
            "tags": []
        }
        self._filter={}
        self._template=""
        self._sockets={}

        if template:
            self._template=template

        if meta:
            for k,v in meta.items():
                self._meta[k]=v
        
        if sockets:
            for k,v in sockets.items():
                self._sockets[k]=v

        if filter:    
            self._filter=filter
        


    def getMeta(self) -> dict:
        """
        Get the meta data of the event.
        Returns:
            dict: The meta data of the event.
        """
        return self._meta

    def getFilter(self) -> dict:
        """
        Get the filter of the event.
        Returns:
            dict: The filter of the event.
        """
        return self._filter
    
    def getTemplate(self) -> str:
        """
        Get the mustache template of the event.
        Returns:
            str: The mustache template of the event.
        """
        return self._template
    
    def getSockets(self) -> dict:
        """
        Get the sockets of the event.
        Returns:
            dict: The sockets of the event.
        """
        return self._sockets
