
from openagents_grpc_proto import rpc_pb2_grpc
from openagents_grpc_proto import rpc_pb2
from .Logger import Logger
from .Disk import Disk
from .RunnerConfig import RunnerConfig
import time
import os
import json
import pickle
from typing import Union

class JobContext:
    """
    A class that represents the context of a job.
    """
    def __init__(self, node: 'OpenAgentsNode',runner:'JobRunner', job: rpc_pb2.Job__pb2):
        self.job=job
        self._node=node
        self.runner=runner
        
        self._cachePath = os.getenv('CACHE_PATH',  "cache")
        if not os.path.exists(self._cachePath):
            os.makedirs(self._cachePath)

        self.logger=Logger(
            self._node.getMeta()["name"]+"."+self.runner.getMeta()["name"],
            self._node.getMeta()["version"],
            self.job.id,
            lambda x: self._node._log(x, self.job.id),
        )

        self._disksByUrl = {}
        self._disksById = {}
        self._diskByName = {}

    def getLogger(self):
        """
        Get the logger of the job.
        """
        return self.logger

 
    def getNode(self):
        """
        Get the node running this job
        """
        return self._node

    def getJob(self):
        """
        Get the job object.
        """
        return self.job

    
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
            self._node.getLogger().error("Error setting cache "+str(e))
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
            self._node.getLogger().error("Error getting cache "+str(e))
            return None


    
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
        if name:self._diskByName[name] = disk
        return disk

    async def close(self):
        """
        Close the job context.
        Free up resources, submit pending logs.
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
        self.logger.close()


    def getJobParamValues(self,key,default:list[str]=None)->list[str]:
        job=self.getJob()
        for p in job.param:
            if p.key == key:
                return p.value or default
        return default

    
    def getJobParamValue(self,key,default:str=None)->str:
        job=self.getJob()
        for p in job.param:
            if p.key == key:
                return p.value[0] or default
        return default 

    def getJobInputs(self,marker:str|None=None)->list[rpc_pb2.JobInput__pb2]:
        job=self.getJob()
        out=[]
        for i in job.input:
            if marker is None or i.marker == marker:
                out.append(i)
        return out

    def getJobInput(self,marker:str|None=None)->rpc_pb2.JobInput__pb2:
        job=self.getJob()
        for i in job.input:
            if marker is None or i.marker == marker:
                return i
        return None

    def getOutputFormat(self):
        job=self.getJob()
        return job.outputFormat
