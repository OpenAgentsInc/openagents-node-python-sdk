import asyncio
import struct

class DiskWriter: 
    """
    A class to write data to a stream.
    """

    def __init__(self,writeQueue: asyncio.Queue, res):
        self.writeQueue = writeQueue
        self.res = res

    async def write(self, data: bytes) -> None:
        """
        Write data to the stream.

        Args:
            data (bytes): The data to write.
        """
        self.writeQueue.put_nowait(data)

    async def writeInt(self, data: int)-> None:
        """
        Write an integer to the stream.
        Note: The integer will be written in big-endian format.

        Args:
            data (int): The integer to write.
        """
        self.writeQueue.put_nowait(data.to_bytes(4, byteorder='big'))

    async def writeUTF8(self, data: str)-> None:
        """
        Write a UTF-8 string to the stream.

        Args:
            data (str): The string to write.
        """
        self.writeQueue.put_nowait(len(data).to_bytes(4, byteorder='big'))
        self.writeQueue.put_nowait(data.encode("utf-8"))
    
    async def writeFloat(self, data: float)-> None:
        """
        Write a float to the stream.
        Note: The float will be written in big-endian format.

        Args:
            data (float): The float to write.
        """
        self.writeQueue.put_nowait(bytearray(struct.pack(">f", data)))

    async def writeDouble(self, data: float)-> None:
        """
        Write a double to the stream.
        Note: The double will be written in big-endian format.

        Args:
            data (float): The double to write.
        """
        self.writeQueue.put_nowait(bytearray(struct.pack(">d", data)))

    async def writeBool(self, data: bool)-> None:
        """
        Write a boolean to the stream.

        Args:
            data (bool): The boolean to write.
        """
        self.writeQueue.put_nowait(data.to_bytes(1, byteorder='big'))
    
    async def writeByte(self, data: int)-> None:
        """
        Write a byte to the stream.

        Args:
            data (int): The byte to write.
        """
        self.writeQueue.put_nowait(data.to_bytes(1, byteorder='big'))

    async def writeShort(self, data: int)-> None:
        """
        Write a short to the stream.
        Note: The short will be written in big-endian format.

        Args:
            data (int): The short to write.
        """
        self.writeQueue.put_nowait(data.to_bytes(2, byteorder='big'))
    
    async def writeLong(self, data: int)-> None:
        """
        Write a long to the stream.
        Note: The long will be written in big-endian format.    

        Args:
            data (int): The long to write.
        """
        self.writeQueue.put_nowait(data.to_bytes(8, byteorder='big'))
    
    async def end(self) -> None:
        """
        End the stream.
        """
        self.writeQueue.put_nowait(None)
        
    async def close(self) -> bool:
        """
        End and close the stream.

        Returns:
            bool: True if the stream was successfully closed, False otherwise.
        """
        self.writeQueue.put_nowait(None)
        res = await self.res
        return res.success

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
