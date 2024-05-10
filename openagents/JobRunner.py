
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
from .JobContext import JobContext
from .Logger import Logger
import asyncio
class JobRunner:
    """
    An abstract class that represents a job runner.
    Implementations of this class should be able to run jobs.
    The internal logic of the runner uses these additional environment variables for configuration:
    - CACHE_PATH: The path to store cached data. Defaults to "./cache".



    """

    def __init__(self, config: RunnerConfig):     
        self._node = None    
        self._template = config.getTemplate()
        self._meta = config.getMeta()
        self._sockets = config.getSockets()
        self._filter = config.getFilter()
        self.runInParallel=False
        self.initialized=False
    
    
        
    
    def getMeta(self):
        return self._meta
    
    def getFilter(self):
        return self._filter

    def getTemplate(self):
        return self._template
    
    def getSockets(self):
        return self._sockets

    def setRunInParallel(self, runInParallel:bool):
        """
        Set whether the runner should run in parallel.
        Args:
            runInParallel (bool): True if the runner should run in parallel, False otherwise. Defaults to False.
        """
        self.runInParallel = runInParallel

    def isRunInParallel(self) -> bool:
        """
        Check if the runner should run in parallel.
        Returns:
            bool: True if the runner should run in parallel, False otherwise.
        """
        return self.runInParallel


    
    async def postRun(self, ctx:JobContext) -> None:
        """
        Called after the runner has finished running.
        Args:
            ctx (JobContext): The context of the job.
        """
        pass

    async def canRun(self,ctx:JobContext) -> bool:
        """
        Check if the runner can run a job.
        Args:
            ctx (JobContext): The context of the job.
        Returns:
            bool: True if the runner can run the job, False otherwise.
        """
        return True
        
    async def preRun(self, ctx:JobContext)-> None:
        """
        Called before the runner starts running.
        Args:
            ctx (JobContext): The context of the job.
        """
        pass

    async def run(self, ctx:JobContext) -> None:
        """
        Run a job.
        Args:
            ctx (JobContext): The context of the job.
        """
        pass

    async def loop(self, node: 'OpenAgentsNode')-> None:
        """
        The main loop of the runner.
        Args:
            node (OpenAgentsNode): The node
        """
        pass


    async def init(self,node: 'OpenAgentsNode')-> None:
        """
        Initialize the runner.
        Args:
            node (OpenAgentsNode): The node
        """
        pass