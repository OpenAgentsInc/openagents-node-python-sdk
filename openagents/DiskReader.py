import asyncio
import struct

class DiskReader: 
    """
    A reader for reading data from a stream.
    """
    def __init__(self, chunksQueue: asyncio.Queue, req):
        self.chunksQueue = chunksQueue
        self.buffer = bytearray()
        self.req = req

    async def read(self, n = 1) -> bytes:
        """
        Read n bytes from the stream.

        Args:
            n (int): The number of bytes to read. Defaults to 1.
        
        Returns:
            bytes: The bytes read from the stream.
        """
        while len(self.buffer) < n:
            v = await self.chunksQueue.get()
            if v is None: break
            self.buffer.extend(v)
        result, self.buffer = self.buffer[:n], self.buffer[n:]
        return result

    async def readInt(self) -> int:
        """
        Read an integer from the stream.
        Note: The integer must be written in big-endian format. 

        Returns:
            int: The integer read from the stream.
        """
        return int.from_bytes(await self.read(4), byteorder='big')
    
    async def readUTF8(self) -> str:
        """
        Read a UTF-8 string from the stream.

        Returns:
            str: The string read from the stream.
        """
        length = await self.readInt()
        return (await self.read(length)).decode("utf-8")

    async def readFloat(self) -> float:
        """
        Read a float from the stream.
        Note: The float must be written in big-endian format.

        Returns:
            float: The float read from the stream.
        """
        return struct.unpack('>f', await self.read(4))[0]
    
    async def readDouble(self) -> float:
        """
        Read a double from the stream.
        Note: The double must be written in big-endian format.

        Returns:
            float: The double read from the stream.
        """
        return struct.unpack('>d', await self.read(8))[0]

    async def readBool(self) -> bool:
        """
        Read a boolean from the stream.

        Returns:
            bool: The boolean read from the stream.
        """
        return bool(await self.read(1))

    async def readByte(self) -> int:
        """
        Read a byte from the stream.

        Returns:
            int: The byte read from the stream.
        """
        return int.from_bytes(await self.read(1), byteorder='big')

    async def readShort(self) -> int:
        """
        Read a short from the stream.
        Note: The short must be written in big-endian format.

        Returns:
            int: The short read from the stream.
        """
        return int.from_bytes(await self.read(2), byteorder='big')

    async def readLong(self) -> int:
        """
        Read a long from the stream.
        Note: The long must be written in big-endian format.

        Returns:
            int: The long read from the stream.
        """
        return int.from_bytes(await self.read(8), byteorder='big')


        
    async def close(self):
        """
        Close the stream.
        
        """
        self.chunksQueue.task_done()
        return await self.req

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


