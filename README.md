# OpenAgents Node - Python SDK


A Python SDK for developing OpenAgents nodes.



## Example

```python
from openagents import JobRunner,OpenAgentsNode,NodeConfig,RunnerConfig

# Define a runner
class MyRunner (JobRunner):
    def __init__(self):
        # Set the runner metadata, template and filters
        super().__init__(\
            RunnerConfig()\
                .kind(5003)\
                .name("My new Runner")\
                .description("This is a new runner")
            # .... See RunnerConfig documentation 
        )


    async def canRun(self,job):
        # Custom job filtering logic
        return True

    async def preRun(self, job):
        # Do something before running the job
        pass

    async def run(self,job):
        # Do something
        print("Running job",job.id)
        # Finish the job
        jobOutput=""
        return jobOutput
    
    async def postRun(self, job):
        # Do something after running the job
        pass

    #async def loop(self):
    #    This is called by the main loop NODE_TPS times per second
    #    Usually you won't need to implement this, but can be useful in some cases



# Initialize the node
myNode = OpenAgentsNode(NodeConfig().name("New node").version("0.0.1").description("This is a new node"))
# Register the runner (you can register multiple runners)
myNode.registerRunner(MyRunner())
# Start the node
myNode.start()

```