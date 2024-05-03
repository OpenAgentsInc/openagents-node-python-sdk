import grpc
from openagents_grpc_proto import rpc_pb2_grpc
from openagents_grpc_proto import rpc_pb2
import time
import os
import traceback
import asyncio
from .JobRunner import JobRunner
from .NodeConfig import NodeConfig
from .Logger import Logger
from typing import Union

class HeaderAdderInterceptor(grpc.aio.UnaryUnaryClientInterceptor):
    """
    An interceptor for GRPC that adds headers to outgoing requests.
    """
    def __init__(self, headers):
        self._headers = headers

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        metadata = client_call_details.metadata
        if not metadata:
            metadata=grpc.aio.Metadata()
        for header in self._headers:
            metadata.add(header[0], header[1])
        new_client_call_details = client_call_details._replace(metadata=metadata)
        response = await continuation(new_client_call_details, request)
        return response

class OpenAgentsNode:
    """
    An OpenAgents node that can run jobs.
    The node can be configured with the following environment variables:
    - NODE_NAME: The name of the node. Defaults to "OpenAgentsNode".
    - NODE_ICON: The icon of the node. Defaults to "".
    - NODE_VERSION: The version of the node. Defaults to "0.0.1".
    - NODE_DESCRIPTION: The description of the node. Defaults to "".
    - POOL_ADDRESS: The address of the pool. Defaults to "
    - POOL_PORT: The port of the pool. Defaults to 5000.
    - POOL_SSL: Whether to use SSL for the pool. Defaults to False.
    - NODE_TPS: The ticks per second of the node main loop. Defaults to 10.
    - NODE_TOKEN: The token of the node. Defaults to None.
    """
  
    def __init__(self, metaOrConfig: Union[dict, NodeConfig]):
        meta=None
        if isinstance(metaOrConfig, NodeConfig):
            meta = metaOrConfig.getMeta()
        else:
            meta = metaOrConfig
        self.nextNodeAnnounce = 0
        self.nodeName = ""
        self.nodeIcon = ""
        self.nodeDescription = ""
        self.channel = None
        self.rpcClient = None
        self.runners=[]
        self.poolAddress = None
        self.poolPort = None
        self.failedJobsTracker = []
        self.isLooping = False
        self.logger = None
        self.loopInterval = 100
        
        name = ""
        icon = ""
        description = ""
        version = "0.0.1"

        name = meta["name"] if "name" in meta else None
        icon = meta["picture"] if "picture" in meta else None
        description = meta["about"] if "about" in meta else None
        version = meta["version"] if "version" in meta else None

        self.nodeName = name or os.getenv('NODE_NAME', "OpenAgentsNode")
        self.nodeIcon = icon or os.getenv('NODE_ICON', "")
        self.nodeVersion = version or os.getenv('NODE_VERSION', "0.0.1")
        self.nodeDescription = description or  os.getenv('NODE_DESCRIPTION', "")

        self.channel = None
        self.rpcClient = None
        self.logger = Logger(self.nodeName,self.nodeVersion)
        self.logger.info("Starting "+self.nodeName+" v"+self.nodeVersion)

    def registerRunner(self, runner:JobRunner) -> None:
        """
        Register a runner to the node.
        Args:
            runner (JobRunner): The runner to register.
        """
        runner.logger=Logger(self.nodeName+"."+runner.__class__.__name__,self.nodeVersion,runner)
        self.runners.append(runner)

    def getLogger(self):
        """
        Get the active logger for the node.
        """
        return self.logger        

    def _getClient(self): 
        """
        Get or create a GRPC client for the node.
        """
        if self.channel is None or self.channel._channel.check_connectivity_state(True)  == grpc.ChannelConnectivity.SHUTDOWN:
            if self.channel is not None:
                try:
                    self.getLogger().info("Closing channel")
                    self.channel.close()
                except Exception as e:
                    self.getLogger().error("Error closing channel "+str(e))
            self.getLogger().info("Connect to "+self.poolAddress+":"+str(self.poolPort)+" with ssl "+str(self.poolSsl))
            
            options=[
                # 20 MB
                ('grpc.max_send_message_length', 1024*1024*20),
                ('grpc.max_receive_message_length', 1024*1024*20)
            ]

            interceptors=None
            nodeToken = os.getenv('NODE_TOKEN', None)
            if nodeToken:
                metadata=[
                    ("authorization", str(nodeToken))
                ]
                if interceptors is None: interceptors=[]
                interceptor=HeaderAdderInterceptor(metadata)        
                interceptors.append(interceptor)
                

            if self.poolSsl:
                self.channel = grpc.aio.secure_channel(self.poolAddress+":"+str(self.poolPort), grpc.ssl_channel_credentials(),options,interceptors=interceptors)
            else:
                self.channel = grpc.aio.insecure_channel(self.poolAddress+":"+str(self.poolPort),options,interceptors=interceptors)
            
            self.rpcClient = rpc_pb2_grpc.PoolConnectorStub(self.channel)
            

        return self.rpcClient

    async def _logToJob(self, message:str, jobId:str=None):
        """
        Log a message to a job.
        Args:
            message (str): The message to log.
            jobId (str): The ID of the job to log to.
        """
        try:
            await self._getClient().logForJob(rpc_pb2.RpcJobLog(jobId=jobId, log=message)) 
        except Exception as e:
            print("Error logging to job "+str(e))

    def _log(self,message:str, jobId:str=None):
        """
        Log a message to the network.
        Args:
            message (str): The message to log.
            jobId (str): The ID of the job to log to.
        """
        if jobId: 
            asyncio.create_task(self._logToJob(message, jobId))
    
    async def _acceptJob(self, jobId:str):
        """
        Accept a job.
        Args:
            jobId (str): The ID of the job to accept.
        """
        await self._getClient().acceptJob(rpc_pb2.RpcAcceptJob(jobId=jobId))

    async def _executePendingJobForRunner(self , runner:JobRunner):
        """
        Execute all pending jobs for a runner.
        Args:
            runner (JobRunner): The runner to execute the job.
        """
        if runner not in self.runners:
            del self.runnerTasks[runner]
            return
        try:
            client = self._getClient()
            #for runner in self.runners:
            jobs=[]
            for filter in runner._filters:
                jobs.extend((await client.getPendingJobs(rpc_pb2.RpcGetPendingJobs(
                    filterByRunOn =  filter["filterByRunOn"] if "filterByRunOn" in filter else None,
                    filterByCustomer = filter["filterByCustomer"] if "filterByCustomer" in filter else None,
                    filterByDescription = filter["filterByDescription"] if "filterByDescription" in filter else None,
                    filterById = filter["filterById"] if "filterById" in filter else None,
                    filterByKind  = filter["filterByKind"] if "filterByKind" in filter else None,
                    wait=60000,
                    # exclude failed jobs
                    excludeId = [x[0] for x in self.failedJobsTracker if time.time()-x[1] < 60]
                ))).jobs)    
            
            for job in jobs:           
                if len(jobs)>0 : runner.getLogger().log(str(len(jobs))+" pending jobs")
                else : runner.getLogger().log("No pending jobs")
                wasAccepted=False
                t=time.time()   
                try:
                    client = self._getClient() # Reconnect client for each job
                    if not await runner.canRun(job):
                        continue
                    await self._acceptJob(job.id)
                    wasAccepted = True
                    runner.getLogger().info("Job started on node "+self.nodeName)  
                    runner._setNode(self)
                    runner._setJob(job)
                    await runner.preRun(job)
                    async def task():
                        try:
                            output=await runner.run(job)    
                            await runner.postRun(job)                            
                            runner.getLogger().info("Job completed in "+str(time.time()-t)+" seconds on node "+self.nodeName, job.id)                
                            await client.completeJob(rpc_pb2.RpcJobOutput(jobId=job.id, output=output))
                        except Exception as e:
                            self.failedJobsTracker.append([job.id, time.time()])
                            runner.getLogger().error("Job failed in "+str(time.time()-t)+" seconds on node "+self.nodeName+" with error "+str(e), job.id)
                            if wasAccepted:
                                await client.cancelJob(rpc_pb2.RpcCancelJob(jobId=job.id, reason=str(e)))
                            traceback.print_exc()
                    asyncio.create_task(task())
                except Exception as e:
                    self.failedJobsTracker.append([job.id, time.time()])
                    runner.getLogger().error("Job failed in "+str(time.time()-t)+" seconds on node "+self.nodeName+" with error "+str(e), job.id)
                    if wasAccepted:
                        await client.cancelJob(rpc_pb2.RpcCancelJob(jobId=job.id, reason=str(e)))
                    traceback.print_exc()
        except Exception as e:
            traceback.print_exc()
            runner.getLogger().error("Error executing runner "+str(e))
            await asyncio.sleep(5000.0/1000.0)
        self.runnerTasks[runner]=asyncio.create_task(self._executePendingJobForRunner(runner))

 
    runnerTasks={}
    async def _executePendingJob(self ):
        """
        Execute all pending jobs for all runners.
        """
        for runner in self.runners:
            try:
                if not runner in self.runnerTasks:
                    self.runnerTasks[runner]=asyncio.create_task(self._executePendingJobForRunner(runner))
            except Exception as e:
                self.getLogger().log("Error executing pending job "+str(e), None)


    async def reannounce(self):    
        """
        Reannounce the node and all templates.
        """
        # Announce node
        try:
            time_ms=int(time.time()*1000)
            if time_ms >= self.nextNodeAnnounce:
                try:
                    client = self._getClient()
                    res=await client.announceNode(rpc_pb2.RpcAnnounceNodeRequest(
                        iconUrl = self.nodeIcon,
                        name = self.nodeName,
                        description = self.nodeDescription,
                    ))
                    self.nextNodeAnnounce = int(time.time()*1000) + res.refreshInterval
                    self.getLogger().log("Node announced, next announcement in "+str(res.refreshInterval)+" ms")
                except Exception as e:
                    self.getLogger().error("Error announcing node "+ str(e), None)
                    self.nextNodeAnnounce = int(time.time()*1000) + 5000

            for runner in self.runners:
                try:
                    if time_ms >= runner._nextAnnouncementTimestamp:
                        client = self._getClient()
                        res = await client.announceEventTemplate(rpc_pb2.RpcAnnounceTemplateRequest(
                            meta=runner._meta,
                            template=runner._template,
                            sockets=runner._sockets
                        ))
                        runner._nextAnnouncementTimestamp = int(time.time()*1000) + res.refreshInterval
                        self.getLogger().log("Template announced, next announcement in "+str(res.refreshInterval)+" ms")
                except Exception as e:
                    self.getLogger().error("Error announcing template "+ str(e), None)
                    runner._nextAnnouncementTimestamp = int(time.time()*1000) + 5000
        except Exception as e:
            self.getLogger().error("Error reannouncing "+str(e), None)
        await asyncio.sleep(5000.0/1000.0)
        asyncio.create_task(self.reannounce())
  
    async def _loop(self):
        """
        The main loop of the node.
        """
        promises = [runner.loop() for runner in self.runners]
        await asyncio.gather(*promises)
        self.isLooping = False
        await asyncio.sleep(self.loopInterval/1000.0)
        asyncio.create_task(self._loop())
        

    async def _run(self, poolAddress=None, poolPort=None, poolSsl=False):
        """
        Internal method to run the node.
        Should not be called, use start() instead.
        """
        await asyncio.sleep(5000.0/1000.0)
        self.poolAddress = poolAddress or os.getenv('POOL_ADDRESS', "127.0.0.1")
        self.poolPort = poolPort or int(os.getenv('POOL_PORT', "5000"))
        self.poolSsl = poolSsl or os.getenv('POOL_SSL', "false")== "true"
        self.loopInterval = 1000.0/int(os.getenv('NODE_TPS', "10"))

        await self._loop()
        await self.reannounce()
        while True:
            await self._executePendingJob()
            await asyncio.sleep(1000.0/1000.0)
        
    def start(self, poolAddress:str=None, poolPort:str=None):
        """
        Start the node in an asyncio event loop.
        Args:
            poolAddress (str): The address of the pool. Defaults to
                the environment variable POOL_ADDRESS.
            poolPort (int): The port of the pool. Defaults to the
                environment variable POOL_PORT.
        """
        asyncio.run(self._run(poolAddress, poolPort))