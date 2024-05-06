# OpenAgents Node - Python SDK


A Python SDK for developing OpenAgents nodes.

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
        # Set the runner metadata, template and filters
        super().__init__(\
            RunnerConfig(
                meta={
                    "kind":5003,
                    "name":"My Action",
                    "description":"This is a new action"
                    "tos": "https://example.com/tos",
                    "privacy": "https://example.com/privacy",
                    "picture": "https://example.com/icon.png",
                    "tags": ["tag1","tag2"]
                    "website": "https://example.com",
                    "author": "John Doe",
                },
                filters=[ 
                    {
                        "filterByKind":5003,
                        #AND
                        "filterByRunOn": "my-new-action"
                    }, # OR
                    {
                        "filterByKind": 5003,
                        #AND
                        "filterByRunOn": "my-new-action-alt"
                    }
                ],
                template="""
                {
                    "kind": {{meta.kind}},
                    "created_at": {{sys.timestamp_seconds}},
                    "tags": [
                        ["param","run-on", "my-new-action" ],                             
                        ["param", "k", "{{in.k}}"],
                        ["output" , "{{out.content}}"]
                        {{#in.queries}}
                        ["i", "{{value}}", "{{type}}", "",  "query"],
                        {{/in.queries}}                       
                        ["expiration", "{{sys.expiration_timestamp_seconds}}"],
                    ],
                    "content":""
                }""",
                sockets={
                    "in": {
                        "k": {
                            "type":"number",
                            "description":"This is a number"
                            "default": "0"
                        },
                        "queries": {
                            "type":"array",
                            "description":"This is an array of queries",
                            "schema": {
                                "value":{
                                    "type":"string",
                                    "description":"This is a query value"
                                }# Last item in schema is repeated for any remaining items
                            }
                        }
                    },
                    "out": {
                        "content": {
                            "type": "string",
                            "description": "The content of the event",
                            "value": "application/json"
                        }
                    }
                }
            )
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
myNode = OpenAgentsNode(NodeConfig(
    meta={
        "name":"My Node",
        "description":"This is a new node"
        "version": "1.0"
    }
))
# Register the runner (you can register multiple runners)
myNode.registerRunner(MyRunner())
# Start the node
myNode.start()

```