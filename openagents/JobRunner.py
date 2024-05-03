
from .Logger import Logger
from .Disk import Disk
from openagents_grpc_proto import rpc_pb2_grpc
from openagents_grpc_proto import rpc_pb2
from .RunnerConfig import RunnerConfig
import time
import os
import json
import pickle
from typing import Union
class JobRunner:
    """
    An abstract class that represents a job runner.
    Implementations of this class should be able to run jobs.
    The internal logic of the runner uses these additional environment variables for configuration:
    - CACHE_PATH: The path to store cached data. Defaults to "./cache".



    """

    def __init__(self, metaOrConfig: Union[dict, RunnerConfig], filters:dict=None, template:dict=None, sockets:dict=None):
        meta=None
        if isinstance(metaOrConfig, RunnerConfig):
            meta = metaOrConfig.getMeta()
            filters = metaOrConfig.getFilters()
            template = metaOrConfig.getTemplate()
            sockets = metaOrConfig.getSockets()
        else:
            meta = metaOrConfig
        self._filters = None
        self._node = None
        self._job = None
        self._disksByUrl = {}
        self._disksById = {}
        self._diskByName = {}
        self._template = None
        self._meta = None
        self._sockets = None
        self._nextAnnouncementTimestamp = 0
        self._cachePath = None

        self.logger = Logger("JobRunner", "0", self, False)
        self._filters = filters
        self._meta = json.dumps(meta)
        self._template = template
        self._sockets = json.dumps(sockets)
        
        self._cachePath = os.getenv('CACHE_PATH',  "cache")
        if not os.path.exists(self._cachePath):
            os.makedirs(self._cachePath)

    
    def getLogger(self) -> Logger:
        """
        Get the active logger for the runner.
        Returns:
            Logger: The logger for the runner.
        """
        return self.logger

    
    async def cacheSet(self, key:str, value, version:int=0, expireAt:int=0, local=True, CHUNK_SIZE=1024*1024*15):
        """
        Set a value in the cache.
        Args:
            key (str): The key of the value to set.
            value (object): The value to set.
            version (int): The version of the cache (if the call to cacheGet requires a different version, the cache will be considered expired). Defaults to 0.            expireAt (int): The timestamp at which the value expires. Defaults to 0.
            expireAt (int): The timestamp at which the value expires in milliseconds. 0 = never. Defaults to 0.
            local (bool): Whether to store the value locally or remotely. Defaults to True.
            CHUNK_SIZE (int): The size of each chunk to write in bytes, if needed. Defaults to 1024*1024*15.
        """
        try:
            dataBytes = pickle.dumps(value)
            if local:
                fullPath = os.path.join(self._cachePath, key)
                with open(fullPath, "wb") as f:
                    f.write(dataBytes)
                with open(fullPath+".meta.json", "w") as f:
                    f.write(json.dumps({"version":version, "expireAt":expireAt}))
            else:
                client = self._node._getClient()
                def write_data():
                    for j in range(0, len(dataBytes), CHUNK_SIZE):
                        chunk = bytes(dataBytes[j:min(j+CHUNK_SIZE, len(dataBytes))])                   
                        request = rpc_pb2.RpcCacheSetRequest(
                            key=key, 
                            data=chunk,
                            expireAt=expireAt,
                            version=version
                        )
                        yield request                              
                res=await client.cacheSet(write_data())
                return res.success
        except Exception as e:
            self.getLogger().error("Error setting cache "+str(e))
            return False
        

    async def cacheGet(self, key:str, lastVersion = 0, local=True) -> any:
        """
        Get a value from the cache.
        Args:
            path (str): The key of the value to get.
            lastVersion (int): The version of the cache to check. Defaults to 0.
            local (bool): Whether to get the value locally or remotely. Defaults to True.
        Returns:
            any: The value of the cache.
        """
        try:
            if local:
                fullPath = os.path.join(self._cachePath, key)
                if not os.path.exists(fullPath) or not os.path.exists(fullPath+".meta.json"):
                    return None
                with open(fullPath+".meta.json", "r") as f:
                    meta = json.loads(f.read())
                if lastVersion > 0 and meta["version"] != lastVersion:
                    return None
                if meta["expireAt"] > 0 and time.time()*1000 > meta["expireAt"]:
                    return None
                with open(fullPath, "rb") as f:
                    return pickle.load(f)
            else:
                client = self._node._getClient()
                bytesOut = bytearray()
                stream = client.cacheGet(rpc_pb2.RpcCacheGetRequest(key=key, lastVersion = lastVersion))
                async for chunk in stream:
                    if not chunk.exists:
                        return None
                    bytesOut.extend(chunk.data)
                return pickle.loads(bytesOut)
        except Exception as e:
            self.getLogger().error("Error getting cache "+str(e))
            return None

    def _setNode(self, node):
        self._node = node

    def _setJob(self, job):
        self._job = job

    def _log(self, message:str):
        """
        Log a message to the network.
        Shouldn't be used directly. Use getLogger().info() instead.
        Args:
            message (str): The message to log.
        """
        if self._job: message+=" for job "+self._job.id
        if self._node: 
            self._node._log(message, self._job.id if self._job else None)
        

    async def openStorage(self, url:str)->Disk:
        """
        Open a storage disk.
        Args:
            url (str): The URL of the disk.
        Returns:
            Disk: The disk object.
        """

        if url in self._disksByUrl:
            return self._disksByUrl[url]
        client = self._node._getClient()
        diskId =(await client.openDisk(rpc_pb2.RpcOpenDiskRequest(url=url))).diskId
        disk =  Disk(id=diskId, url=url, node=self._node)
        self._disksByUrl[url] = disk
        self._disksById[diskId] = disk
        return disk

    async def createStorage(self,name:str=None,encryptionKey:str=None,includeEncryptionKeyInUrl:str=None) -> Disk:
        """
        Create a storage disk.
        Args:
            name (str): Optional: The name of the disk.
            encryptionKey (str): Optional: The encryption key of the disk.
            includeEncryptionKeyInUrl (str): Optional: Whether to include the encryption key in the URL.
        Returns:
            Disk: The disk object.
        """
        if name in self._diskByName:
            return self._diskByName[name]
        
        client = self._node._getClient()
        url = (await client.createDisk(rpc_pb2.RpcCreateDiskRequest(
            name=name,
            encryptionKey=encryptionKey,
            includeEncryptionKeyInUrl=includeEncryptionKeyInUrl
        ))).url
        diskId =( await client.openDisk(rpc_pb2.RpcOpenDiskRequest(url=url))).diskId
        disk = Disk(id=diskId, url=url, node=self._node)
        self._disksByUrl[url] = disk
        self._disksById[diskId] = disk
        self._diskByName[name] = disk
        return disk

    async def postRun(self, job:rpc_pb2.Job__pb2.Job) -> None:
        """
        Called after the runner has finished running.
        """
        for disk in self._disksById.values():
            await disk.close()
        for disk in self._disksByUrl.values():
            await disk.close()
        for disk in self._diskByName.values():
            await disk.close()
        self._disksById = {}
        self._disksByUrl = {}
        self._diskByName = {}

    async def canRun(self,job:rpc_pb2.Job__pb2.Job) -> bool:
        """
        Check if the runner can run a job.
        Args:
            job (Job): The job to check.
        Returns:
            bool: True if the runner can run the job, False otherwise.
        """
        return True
        
    async def preRun(self, job:rpc_pb2.Job__pb2.Job)-> None:
        """
        Called before the runner starts running.
        """
        pass

    async def loop(self)-> None:
        """
        The main loop of the runner.
        """
        pass

    async def run(self, job:rpc_pb2.Job__pb2.Job) -> None:
        """
        Run a job.
        """
        pass