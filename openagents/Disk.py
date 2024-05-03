

import asyncio
import grpc
import struct

from openagents_grpc_proto import rpc_pb2_grpc
from openagents_grpc_proto import rpc_pb2
from .DiskReader import DiskReader
from .DiskWriter import DiskWriter
from typing import List

class Disk:
    """
    A virtual p2p disk on the OpenAgents network.
    """

    def __init__(self, id: str, url: str, node):
        self.id = id
        self.url = url
        self.node = node
        self.closed = False
    
    async def list(self, prefix:str="/") -> list[str]:
        """
        List files in the disk with the given prefix.

        Args:
            prefix (str): The prefix to filter files. Defaults to "/".
        
        Returns:
            list[str]: A list of file paths.
        """
        client = self.node._getClient()
        files = await client.diskListFiles(rpc_pb2.RpcDiskListFilesRequest(diskId=self.id, path=prefix))
        return files.files
    
    async def delete(self, path:str) -> bool:
        """
        Delete a file from the disk.

        Args:
            path (str): The path of the file to delete.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        client = self.node._getClient()
        res = await client.diskDeleteFile(rpc_pb2.RpcDiskDeleteFileRequest(diskId=self.id, path=path))
        return res.success

    async def writeBytes(self, path:str, dataBytes:bytes, CHUNK_SIZE:int=1024*1024*15) -> bool:
        """
        Write bytes to a file on the disk.

        This method is deprecated. Use 
            async with disk.openwriteStream(path) as writer:
                await writer.write(data)
        instead.

        Args:
            path (str): The path of the file to write.
            dataBytes (bytes): The bytes to write.
            CHUNK_SIZE (int): The size of each chunk to write. Defaults to 1024*1024*15.

        Returns:
            bool: True if the bytes were written successfully, False otherwise.
        """
        client = self.node._getClient()
        def write_data():
            for j in range(0, len(dataBytes), CHUNK_SIZE):
                chunk = bytes(dataBytes[j:min(j+CHUNK_SIZE, len(dataBytes))])                   
                request = rpc_pb2.RpcDiskWriteFileRequest(diskId=str(self.id), path=path, data=chunk)
                yield request                              
        res=await client.diskWriteFile(write_data())
        return res.success


    async def openWriteStream(self, path:str, CHUNK_SIZE:int= 1024*1024*15) -> DiskWriter:
        """
        Open a stream for writing data to a file on the disk.

        Args:
            path (str): The path of the file to write.
            CHUNK_SIZE (int): The size of each chunk to write. Defaults to 1024*1024*15.

        Returns:
            DiskWriter: A writer for writing data to the stream.
        """
        client = self.node._getClient()
        writeQueue = asyncio.Queue()             
        async def write_data():
            while True:
                dataBytes = await writeQueue.get()
                if dataBytes is None:  # End of stream
                    break
                for j in range(0, len(dataBytes), CHUNK_SIZE):
                    chunk = bytes(dataBytes[j:min(j+CHUNK_SIZE, len(dataBytes))])                   
                    request = rpc_pb2.RpcDiskWriteFileRequest(diskId=str(self.id), path=path, data=chunk)
                    yield request
                writeQueue.task_done()
        res=client.diskWriteFile(write_data())
        return DiskWriter(writeQueue, res)

    
    async def openReadStream(self, path:str)-> DiskReader:
        """
        Open a stream for reading data from a file on the disk.

        Args:
            path (str): The path of the file to read.

        Returns:
            DiskReader: A reader for reading data from the stream.
        """

        client = self.node._getClient()
        readQueue = asyncio.Queue()
        async def read_data():
            async for chunk in client.diskReadFile(rpc_pb2.RpcDiskReadFileRequest(diskId=self.id, path=path)):
                readQueue.put_nowait(chunk.data)
        r = asyncio.create_task(read_data())
        return DiskReader(readQueue, r)

    async def readBytes(self, path:str):
        """
        Read bytes from a file on the disk.

        This method is deprecated. Use
            async with disk.openReadStream(path) as reader:
                data = await reader.read()

        Args:
            path (str): The path of the file to read.

        Returns:
            bytes: The bytes read from the file.
        """
        client = self.node._getClient()
        bytesOut = bytearray()
        async for chunk in client.diskReadFile(rpc_pb2.RpcDiskReadFileRequest(diskId=self.id, path=path)):
            bytesOut.extend(chunk.data)
        return bytesOut

    async def writeUTF8(self, path:str, data:str) -> bool:
        """
        Write a UTF-8 string to a file on the disk.

        This method is deprecated. Use
            async with disk.openWriteStream(path) as writer:
                await writer.writeUTF8(data)
        
        Args:
            path (str): The path of the file to write.
            data (str): The string to write.

        Returns:
            bool: True if the string was written successfully, False otherwise.
        """
        return await self.writeBytes(path, data.encode('utf-8'))

    async def readUTF8(self, path:str)-> str:
        """
        Read a UTF-8 string from a file on the disk.

        This method is deprecated. Use
            async with disk.openReadStream(path) as reader:
                data = await reader.readUTF8()

        Args:
            path (str): The path of the file to read.

        Returns:
            str: The string read from the file.
        """
        return (await self.readBytes(path)).decode('utf-8')


    
    async def close(self)-> None:
        """
        Close the disk.
        """
        if self.closed: return
        client = self.node._getClient()
        await client.closeDisk(rpc_pb2.RpcCloseDiskRequest(diskId=self.id))
        self.closed=True

    def getUrl(self)-> str:
        """
        Get the URL that can be used by any node to access the disk.

        Returns:
            str: The URL of the disk.
        """
        return self.url

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


