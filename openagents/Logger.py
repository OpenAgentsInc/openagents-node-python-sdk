import time
import os
import concurrent
from threading import Condition
import queue
from typing import Literal
import base64
import requests
import traceback
LogLevel = Literal[
    "error",
    "warn",
    "info",
    "debug",
    "fine",
    "finer",
    "finest"
]

class OpenObserveLogger:
    """
    A logger for OpenObserve that sends logs in batches.
    """
    def __init__(self, options:dict):
        self.options = options        
        self.batchSize= self.options["batchSize"]
        self.flushInterval = self.options["flushInterval"]
        if not self.flushInterval:
            self.flushInterval = 5000
        if not self.batchSize:
            self.batchSize = 21        
        self.buffer = queue.Queue()
        self.wait = Condition()
        self.flushThread = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        self.flushThread.submit(self.flushLoop)
        

    def batchReady(self):
        with self.wait:
            self.wait.notify_all()

    def log(self, level:LogLevel, message:str, timestamp:int=None):
        """
        Log a message with a specific level.

        Args:
            level (LogLevel): The level of the log.
            message (str): The message to log.
            timestamp (int): The timestamp of the log. Defaults to the current time.
        """
        log_entry = {
            'level': level,
            '_timestamp': timestamp or int(time.time()*1000),
            'log': message
        }
        meta=self.options["meta"] if "meta" in self.options else {}
        for key in meta:
            log_entry[key]=meta[key]

        self.buffer.put(log_entry)
        if self.buffer.qsize() >= self.batchSize:
            self.flushThread.submit(self.batchReady)

    def _close(self):
        while not self.buffer.empty():
            with self.wait:
                self.wait.notify_all()
            time.sleep(0.1)
        self.flushThread.shutdown()
        
    def close(self):
        """
        Immediately flush all the logs to OpenObserve and shutdown the logger.
        """
        self.flushThread.submit(self._close)        
            
        
    def _flushToOpenObserve(self, batch):
        if len(batch) == 0:
            return
        try:
            url = self.options["baseUrl"]+"/api/"+self.options["org"]+"/"+self.options["stream"]+"/_json"   
            basicAuth = self.options["auth"]
            if not isinstance(basicAuth, str):
                if "username" in basicAuth and "password" in basicAuth:
                    basicAuth = basicAuth["username"]+":"+basicAuth["password"]
                    basicAuth = base64.b64encode(basicAuth.encode()).decode()
            headers = {
                'Content-Type': 'application/json',
                "Authorization": "Basic "+basicAuth if basicAuth else None
            }
            res = requests.post(url, headers=headers, json=batch)
            if res.status_code != 200:
                print("Error flushing log "+str(res.status_code))
        except Exception as e:
            print("Error flushing log "+str(e))


    def flushLoop(self):
        while True:
            with self.wait:
                self.wait.wait(self.flushInterval/1000)
            batch = []
            while not self.buffer.empty() and len(batch) < self.batchSize:
                try:
                    batch.append(self.buffer.get(block=False))
                except queue.Empty:
                    break         
            self._flushToOpenObserve(batch)


    


class Logger :
    """
    A logger for OpenAgents Nodes.
    The logger can be configured with the following environment variables:
    - LOG_LEVEL: The minimum level of logs to print. Defaults to "debug".
    - OPENOBSERVE_LOGLEVEL: The minimum level of logs to send to OpenObserve. Defaults to the value of LOG_LEVEL.
    - OPENOBSERVE_ENDPOINT: The endpoint of the OpenObserve server.
    - OPENOBSERVE_ORG: The organization to log to. Defaults to "default".
    - OPENOBSERVE_STREAM: The stream to log to. Defaults to "default".
    - OPENOBSERVE_BASICAUTH: The basic authentication to use for logging.
    - OPENOBSERVE_USERNAME: The username for basic authentication.
    - OPENOBSERVE_PASSWORD: The password for basic authentication.
    - OPENOBSERVE_BATCHSIZE: The batch size for logging to OpenObserve. Defaults to 21.
    - OPENOBSERVE_FLUSHINTERVAL: The flush interval for logging to OpenObserve. Defaults to 5000.

    """

    def __init__(self, name:str, version:str, jobId:str=None, runnerLogger=None, level=None, enableOobs:bool=True):
        """
        Create a new logger.
        Args:
            name (str): The name of the logger.
            version (str): The version of the logger.
            runnerLogger : The function to log to the runner.
            level (LogLevel): Optional: The minimum level of logs to print. Defaults to environment variable or "debug".
            enableOobs (bool): Optional: Whether to enable logging to OpenObserve. Defaults to True.
        """
        self.name=name or "main"
        self.runnerLogger=runnerLogger
        self.logLevel=None
        self.oobsLogger=None
        self.version=version
        self.jobId=jobId
        
        logLevelName = os.getenv('LOG_LEVEL', "finer" if not os.getenv('PRODUCTION', None) else "info")
        oobsLogLevelName= os.getenv('OPENOBSERVE_LOGLEVEL', "info")

        self.logLevel = self._levelToValue(logLevelName)
        self.oobsLogLevel = self._levelToValue(oobsLogLevelName)
        
        if level and self._levelToValue(level) > self.logLevel:
            self.logLevel = self._levelToValue(level)

        if level and self._levelToValue(level) > self.oobsLogLevel:
            self.oobsLogLevel = self._levelToValue(level)

        oobsEndPoint = os.getenv('OPENOBSERVE_ENDPOINT', None)
        if enableOobs and oobsEndPoint:
            
            self.oobsLogger = OpenObserveLogger({
                "baseUrl": oobsEndPoint,
                "org": os.getenv('OPENOBSERVE_ORG', "default"),
                "stream": os.getenv('OPENOBSERVE_STREAM', "default"),
                "auth": os.getenv('OPENOBSERVE_BASICAUTH', None) or {
                    "username": os.getenv('OPENOBSERVE_USERNAME', None),
                    "password": os.getenv('OPENOBSERVE_PASSWORD', None)
                },
                "batchSize": int(os.getenv('OPENOBSERVE_BATCHSIZE', 21)),
                "flushInterval": int(os.getenv('OPENOBSERVE_FLUSHINTERVAL', 0)),
                "meta":{
                    "appName": self.name,
                    "appVersion": self.version,
                    "jobId": self.jobId
                }                
            })

    def _levelToValue(self, level:LogLevel)->int:
        if level == "error": return 7
        if level == "warn": return 6
        if level == "info": return 5
        if level == "debug": return 4
        if level == "fine": return 3
        if level == "finer": return 2
        if level == "finest": return 1
        return 1

    def _log(self, level: LogLevel, args:tuple):
        message = " ".join([str(x) for x in args])

        levelV=self._levelToValue(level)
        minLevel = self.logLevel
        minObsLevel = self.oobsLogLevel
        minNostrLevel = self._levelToValue("info")

        if levelV >= minLevel:
            date = time.strftime("%Y-%m-%d %H:%M:%S")
            print(date+" ["+self.name+":"+self.version+"] "+(("("+self.jobId+")") if self.jobId else "")+": "+level+" : "+message)

        if self.oobsLogger and levelV >= minObsLevel:
            self.oobsLogger.log(level, message)
        
        if self.runnerLogger and levelV >= minNostrLevel:
            self.runnerLogger(message)


    def log(self, *args):
        self._log("debug", args)
    
    def info(self, *args):
        self._log("info", args)
    
    def warn(self, *args):
        self._log("warn",   args)
    
    def error(self, *args):
        self._log("error", args)
        traceback.print_exc()

    def debug(self, *args):
        self._log("debug", args)
    
    def fine(self, *args):
        self._log("fine",  args)
    
    def finer(self, *args):
        self._log("finer",  args)

    def finest(self, *args):
        self._log("finest", args)

    def close(self):
        if self.oobsLogger:
            self.oobsLogger.close()


       