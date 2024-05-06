

from typing import Literal
from typing import Union,Type
from typing import TypeVar

SocketType = Literal[
    "number",
    "string",
    "map",
    "array",
    "boolean"
]

T = TypeVar('T', bound='AbstractSocketBuilder')



class AbstractSocketBuilder:
    def __init__(self, socketFactory:Union['SockerFactory','MapSchemaBuilder','ArraySocketBuilder'], sockets, stype:SocketType,  name:str):
        self._type=stype
        self._socketFactory=socketFactory
        sockets[name]=self._socket={
            "type": stype,
            "description": "",
            "name": name
        }

    def name(self:T ,name:str)->T :
        """
        Set the full name of the socket.
        Args:
            name (str): The name of the socket.
        Returns:
            AbstractSocketBuilder: The socket builder.
        """
        self._socket["name"]=name
        return self

    def description(self:T ,description:str)->T :
        """
        Set the description of the socket.
        Args:
            description (str): The description of the socket.
        Returns:
            AbstractSocketBuilder: The socket builder.
        """
        self._socket["description"]=description
        return self

    def defaultValue(self: T ,defaultValue:Union[int,float,str,bool])->T :
        """
        Set the default value of the socket.
        Args:
            defaultValue (Union[int,float,str,bool]): The default value of the socket.
        Returns:
            AbstractSocketBuilder: The socket builder.
        """
        self._socket["value"]=defaultValue
        return self

    def commit(self) -> Union['SockerFactory','MapSchemaBuilder','ArraySocketBuilder']:
        """
        Return to the socket factory.
        Returns:
            SocketFactory: The socket factory.
        """
        return self._socketFactory


class NumberSocketBuilder(AbstractSocketBuilder):
    """
    A class to build a number socket.
    """
    def __init__(self, socketBuilder, sockets, name:str):
        super().__init__(socketBuilder, sockets, "number", name)
   

    def defaultValue(self,defaultValue:Union[int,float])->'NumberSocketBuilder':
        """
        Set the default value of the socket.
        Args:
            defaultValue (Union[int,float]): The default value of the socket.
        Returns:
            NumberSocketBuilder: The socket builder.
        """
        super().defaultValue(defaultValue)
        return self

    
class StringSocketBuilder(AbstractSocketBuilder):
    """
    A class to build a string socket.
    """

    def __init__(self, socketBuilder, sockets, name:str):
        super().__init__(socketBuilder, sockets, "string", name)
   

    def defaultValue(self,defaultValue:str)->'StringSocketBuilder':
        """
        Set the default value of the socket.
        Args:
            defaultValue (str): The default value of the socket.
        Returns:
            StringSocketBuilder: The socket builder.
        """
        super().defaultValue(defaultValue)
        return self

class BooleanSocketBuilder(AbstractSocketBuilder):
    """
    A class to build a boolean socket.
    """

    def __init__(self, socketBuilder, sockets, name:str):
        super().__init__(socketBuilder, sockets, "boolean", name)
   

    def defaultValue(self,defaultValue:bool)->'BooleanSocketBuilder':
        """
        Set the default value of the socket.
        Args:
            defaultValue (bool): The default value of the socket.
        Returns:
            BooleanSocketBuilder: The socket builder.   
        """
        super().defaultValue(defaultValue)
        return self

class MapSchemaBuilder:
    """
    A class to build a map schema.
    """

    def __init__(self, mapBuilder, schema):
        self._mapBuilder=mapBuilder
        self._schema=schema   

    def field(self, name:str,stype:SocketType )->Union['NumberSocketBuilder','StringSocketBuilder','BooleanSocketBuilder','MapSocketBuilder','ArraySocketBuilder']:
        """
        Add a field to the map schema.
        Args:
            name (str): The name of the field.
            stype (SocketType): The type of the field.
        Returns:
            AbstractSocketBuilder: The socket builder for the field.
        """
        return selectBuilder(self,self._schema,stype,name)
        
    def commit(self) -> 'MapSocketBuilder':
        """
        Return to the map builder.
        Returns:
            MapSocketBuilder: The map builder.
        """
        return self._mapBuilder

class ArraySchemaBuilder:
    """
    A class to build an array schema.
    """
    def __init__(self, arrayBuilder, schema):
        self._arrayBuilder=arrayBuilder
        self._schema=schema   

    def field(self, name:str,stype:SocketType )->Union['NumberSocketBuilder','StringSocketBuilder','BooleanSocketBuilder','MapSocketBuilder','ArraySocketBuilder']:
        """
        Add a field to the array schema.
        Note: the last specified field will be repeated for any remaining values.
        Args:
            name (str): The name of the field.
            stype (SocketType): The type of the field.
        Returns:
            AbstractSocketBuilder: The socket builder for the field.
        """        

        return selectBuilder(self,self._schema,stype,name)
        
    def commit(self) -> 'ArraySocketBuilder':
        """
        Return to the array builder.
        Returns:
            ArraySocketBuilder: The array builder.
        """
        return self._arrayBuilder
    




class MapSocketBuilder(AbstractSocketBuilder):
    """
    A class to build a map socket.
    """

    def __init__(self, socketBuilder, sockets, name:str):
        super().__init__(socketBuilder, sockets, "map", name)
   

    def schema(self)->MapSchemaBuilder:
        """
        Specify the layout of the map socket.
        Returns:
            MapSchemaBuilder: The map schema builder.
        """
        schema=self._socket["schema"]={}
        return  MapSchemaBuilder(self,schema)

class ArraySocketBuilder(AbstractSocketBuilder):
    def __init__(self, socketBuilder, sockets, name:str):
        super().__init__(socketBuilder, sockets, "array", name)
   

    def schema(self)->ArraySchemaBuilder:
        """
        Specify the layout of the array socket.
        Returns:
            ArraySchemaBuilder: The array schema builder.
        """

        schema=self._socket["schema"]={}
        return  ArraySchemaBuilder(self,schema)

class SocketFactory:
    """
    A class to build sockets for an event.
    """
    def __init__(self, econfig, sockets):
        self._sockets=sockets
        self._econfig=econfig

    
       
 
    def inSocket(self, name:str, stype:SocketType)->Union['NumberSocketBuilder','StringSocketBuilder','BooleanSocketBuilder','MapSocketBuilder','ArraySocketBuilder']:
        """
        Add an input socket to the event.
        Args:
            name (str): The name of the socket.
            stype (SocketType): The type of the socket.
        Returns:
            AbstractSocketBuilder: The socket builder for the given type.
        """
        inSockets=None
        if "in" in self._sockets:
            inSockets=self._sockets["in"]
        else:
            inSockets={}
            self._sockets["in"]=inSockets

        return selectBuilder(self,inSockets,stype,name)
        
    def outSocket(self,name:str,stype:SocketType)->Union['NumberSocketBuilder','StringSocketBuilder','BooleanSocketBuilder','MapSocketBuilder','ArraySocketBuilder']:
        """
        Add an output socket to the event.
        Args:
            name (str): The name of the socket.
            stype (SocketType): The type of the socket.
        Returns:
            AbstractSocketBuilder: The socket builder for the given type.
        """
        outSockets=None
        if "out" in self._sockets:
            outSockets=self._sockets["out"]
        else:
            outSockets={}
            self._sockets["out"]=outSockets

        return selectBuilder(self,outSockets,stype,name)

    def commit(self) -> 'EventConfig':
        """
        Return to the event configuration.
        Returns:
            EventConfig: The event configuration.
        """
        return self._econfig

class FilterBuilder:
    """
    A class to build filters for an event.
    """
    def __init__(self, econfig, filters):
        self._filter={}
        self._filters=filters
        self._filters.append(self._filter)
        self._econfig=econfig

    def filterByRunOn(self,runOn:str)->'FilterBuilder':
        """
        Filter the event by run on param.
        Args:
            runOn (str): a regex to filter the event.
        Returns:
            FilterBuilder: The filter builder.
        """
        self._filter["filterByRunOn"]=runOn
        return self

    def filterByCustomer(self,customer:str)->'FilterBuilder':
        """
        Filter the event by customer.
        Args:
            customer (str): a regex to filter the event.
        Returns:
            FilterBuilder: The filter builder.
        """
        self._filter["filterByCustomer"]=customer
        return self

    def filterByDescription(self,description:str)->'FilterBuilder':
        """
        Filter the event by description.
        Args:
            description (str): a regex to filter the event.
        Returns:
            FilterBuilder: The filter builder.
        """
        self._filter["filterByDescription"]=description
        return self

    def filterById(self,id:str)->'FilterBuilder':
        """
        Filter the event by id.
        Args:
            id (str): a regex to filter the event.
        Returns:
            FilterBuilder: The filter builder.
        """
        self._filter["filterById"]=id
        return self

    def filterByKind(self,kind:int)->'FilterBuilder':
        """
        Filter the event by kind.
        Args:
            kind (int): the event kind to filter.
        Returns:
            FilterBuilder: The filter builder.
        """

        self._filter["filterByKind"]=kind
        return self

    def OR(self)->'FilterBuilder':
        """
        Add another filter with an OR condition.
        Returns:
            FilterBuilder: The filter builder.
        """
        return FilterBuilder(self._econfig,self._filters)

    def commit(self)->'EventConfig':
        """
        Return to the event configuration.
        Returns:
            EventConfig: The event configuration.
        """
        return self._econfig

class RunnerConfig:
    """
    A class to build an event (meta, template, socket schema, filters).
    """
    def __init__(self, meta:dict=None, filters:list[dict]=None, template:str=None, sockets:dict=None):
        self._meta={
            "kind": 5003,
            "name": "An event template",
            "about": "",
            "description": "",
            "tos": "",
            "privacy": "",
            "author": "",
            "web": "",
            "picture": "",
            "tags": []
        }
        self._filters=[]
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

        if filters:    
            for f in filters:
                self._filters.append(f)
        


    def getMeta(self) -> dict:
        """
        Get the meta data of the event.
        Returns:
            dict: The meta data of the event.
        """
        return self._meta

    def getFilters(self) -> dict:
        """
        Get the filters of the event.
        Returns:
            dict: The filters of the event.
        """
        return self._filters
    
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

    def kind(self,kind:int)->'EventConfig':
        """
        Set the kind of the event.
        Args:
            kind (int): The kind of the event.
        Returns:
            EventConfig: The event configuration.
        """
        self._meta["kind"]=kind
        return self

    def name(self,name:str)->'EventConfig':
        """
        Set the name of the event.
        Args:
            name (str): The name of the event.
        Returns:
            EventConfig: The event configuration.
        """
        self._meta["name"]=name
        return self

    def description(self,description:str)->'EventConfig':
        """
        Set the description of the event.
        Args:
            description (str): The description of the event.
        Returns:
            EventConfig: The event configuration.
        """
        self._meta["about"]=description
        self._meta["description"]=description
        return self

    def tos(self,tos:str)->'EventConfig':
        """
        Set the terms of service of the event.
        Args:
            tos (str): The terms of service of the event.
        Returns:
            EventConfig: The event configuration.
        """
        self._meta["tos"]=tos
        return self

    def privacy(self,privacy:str)->'EventConfig':
        """
        Set the privacy of the event.
        Args:
            privacy (str): The privacy of the event.
        Returns:
            EventConfig: The event configuration.
        """
        self._meta["privacy"]=privacy
        return self
    
    def author(self,author:str)->'EventConfig':
        """
        Set the author of the event.
        Args:
            author (str): The author of the event.
        Returns:
            EventConfig: The event configuration.
        """
        self._meta["author"]=author
        return self

    def website(self,web:str)->'EventConfig':
        """
        Set the web of the event.
        Args:
            web (str): The web of the event.
        Returns:
            EventConfig: The event configuration.
        """
        self._meta["web"]=web
        return self
    
    def picture(self,picture:str)->'EventConfig':
        """
        Set the picture of the event.
        Args:
            picture (str): The picture of the event.
        Returns:
            EventConfig: The event configuration.
        """
        self._meta["picture"]=picture
        return self
    
    def tags(self,tags:list[str])->'EventConfig':
        """
        Set the tags of the event.
        Args:
            tags (List[str]): The tags of the event.
        Returns:
            EventConfig: The event configuration.
        """
        self._meta["tags"]=tags
        return self

    def filters(self)->FilterBuilder:
        """
        Return the filter builder to add filters to the event.
        Returns:
            FilterBuilder: The filter builder.
        """
        return FilterBuilder(self,self._filters)
    
    def template(self,template:str)->SocketFactory:
        """
        Set the template of the event.
        The template can access to 
            - all the meta data of the event using meta. prefix (eg. meta.kind).
            - system variables using sys. prefix (eg. sys.timestamp_seconds).
            - all the socket of the event using in. and out. prefix (eg. in.data).
        Args:
            template (str): A mustache template for the event.
        Returns:
            SocketFactory: The socket factory for the event.
        """
        self._template=template
        return SocketFactory(self, self._sockets)

 
def selectBuilder(parent:Union[SocketFactory,MapSchemaBuilder,ArraySocketBuilder],output,stype,name) -> Union['NumberSocketBuilder','StringSocketBuilder','BooleanSocketBuilder','MapSocketBuilder','ArraySocketBuilder']:
    if stype=="number":
        return NumberSocketBuilder(parent,output,name)
    elif stype=="string":
        return StringSocketBuilder(parent,output,name)
    elif stype=="boolean":
        return BooleanSocketBuilder(parent,output,name)
    elif stype=="map":
        return MapSocketBuilder(parent,output,name)
    elif stype=="array":
        return ArraySocketBuilder(parent,output,name)
    else:
        raise Exception("Invalid type")
