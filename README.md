# OpenAgents Node - Python SDK


A Python SDK for developing OpenAgents nodes.

## Requirements
- Python 3.11 or higher

## Installation

```bash
pip install openagents-node-sdk
```

## Usage Example

```python
from openagents import JobRunner,OpenAgentsNode,NodeConfig,RunnerConfig

# Define a runner
class MyRunner (JobRunner):
    def __init__(self):
        # Set the runner metadata, template and filter
        super().__init__(
            RunnerConfig(
                meta={
                    "kind":5003,
                    "name":"My Action",
                    "description":"This is a new action",
                    "tos": "https://example.com/tos",
                    "privacy": "https://example.com/privacy",
                    "picture": "https://example.com/icon.png",
                    "tags": ["tag1","tag2"],
                    "website": "https://example.com",
                    "author": "John Doe"
                },
                # Filters are regular expressions that are used to define which jobs this runner can run
                filter={
                    "filterByKind": "5003",
                    #AND
                    "filterByRunOn": "my-new-action"
                },
                # Mustache template (https://mustache.github.io/)
                template=""" 
                {
                    "kind": {{meta.kind}},
                    "created_at": {{sys.timestamp_seconds}},
                    "tags": [
                        ["param","run-on", "my-new-action" ],                             
                        ["param", "k", "{{in.k}}"],
                        ["output" , "{{in.outputType}}"],
                        {{#in.queries}}
                        ["i", "{{value}}", "{{type}}", "",  "query"],
                        {{/in.queries}}                       
                        ["expiration", "{{sys.expiration_timestamp_seconds}}"],
                    ],
                    "content":""
                }""",
                 # In JSON Schema format (https://json-schema.org/)
                sockets={
                    "in": {
                        "k": {
                            "title": "MyNumber",
                            "description":"This is a number",
                            "type":"integer",
                            "default": 0,
                        },
                        "queries": {
                            "title": "MyArray",
                            "type":"array",
                            "description":"This is an array of strings",
                            "items": {
                                "type":"string"
                            }
                        },
                        "outputType": {
                            "title": "Output Type",
                            "type": "string",
                            "description": "The output type of the event",
                            "default": "application/json"
                        }
                    },
                    "out": {
                        "output": {
                            "title": "Output",
                            "type": "string",
                            "description": "The output content"
                        }
                    }
                }
            )
        )

    async def init(self, node):
       # Initialize class
       pass

    async def canRun(self,ctx):
        # Custom job filtering logic
        return True

    async def preRun(self, ctx):
        # Do something before running the job
        pass

    async def run(self,ctx):
        # Do something
        print("Running job",job.id)
        # Finish the job
        jobOutput=""
        return jobOutput
    
    async def postRun(self, ctx):
        # Do something after running the job
        pass

    #async def loop(self, node):
    #    This is called by the main loop NODE_TPS times per second
    #    Usually you won't need to implement this, but can be useful in some cases



# Initialize the node
myNode = OpenAgentsNode(NodeConfig(
    meta={
        "name":"My Node",
        "description":"This is a new node",
        "version": "1.0"
    }
))

# Register the runner (you can register multiple runners)
myNode.registerRunner(MyRunner())
# Start the node
myNode.start()
```
For more information check the [OpenAgents Python SDK Documentation](https://docs.openagents.com/python-sdk)

----
*Note: By default the node will connect to OpenAgents open pool *(playground.openagents.com 6021 ssl)*, this can be changed by setting the following environment variables:*

```bash
POOL_ADDRESS="playground.openagents.com" # custom pool address
POOL_PORT="6021" #  custom pool port
POOL_SSL="true" # or "false"
```
*To learn how to host your own pool check the [Running a Pool](https://docs.openagents.com/running-a-pool) documentation.*


