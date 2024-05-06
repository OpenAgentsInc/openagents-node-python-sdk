import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from openagents import NodeConfig
from openagents import RunnerConfig


def test_nodeconfig():
    nodeConfig = NodeConfig().name("TestNode").version("0.1").description("A test node")
    meta = nodeConfig.getMeta()
    print(meta)


def test_eventconfig():
    runnerConfig = RunnerConfig() \
        .kind(1) \
        .name("TestEvent") \
        .description("A test event") \
        .tos("Test TOS") \
        .privacy("Test Privacy") \
        .author("Test Author") \
        .picture("Test Picture") \
        .website("Test Website") \
        .tags(["Test", "Tag"]) 

    runnerConfig.filters().filterByCustomer("test").filterByDescription("test").OR().filterByKind(1).commit()

    template = runnerConfig.template("""{
        "kind": {{meta.kind}},
        "created_at": {{sys.timestamp_seconds}},
        "tags": [
            ["param","run-on", "openagents/search" ],                             
            ["param", "k", "{{in.k}}"],
            ["param", "normalize", "{{in.normalize}}"],
            {{#in.queries}}
            ["i", "{{value}}", "{{type}}", "",  "query"],
            {{/in.queries}}
            {{#in.indices}}
            ["i", "{{value}}", "{{type}}", "",  "index"],
            {{/in.indices}}
            ["expiration", "{{sys.expiration_timestamp_seconds}}"],
        ],
        "content":""
    }
    """)
    template.inSocket("k", "number").description("The number of results to return").defaultValue(1)
    template.inSocket("normalize", "boolean").description("Normalize index").defaultValue(True)

    queries = template.inSocket("queries", "array").description("The queries to run").schema()
    queries.field("value", "string").description("The query to run")
    queries.field("type", "string").description("The type of query")

    print(runnerConfig.getMeta())
    print(runnerConfig.getFilters())
    print(runnerConfig.getTemplate())
    print(runnerConfig.getSockets())
    

def test_from_json():
    containerName="openagents/search"

    config=RunnerConfig(meta={
        "kind": 1,
        "name": "TestEvent",
        "description": "A test event",
        "tos": "Test TOS",
        "privacy": "Test Privacy",
        "author": "Test Author",
        "picture": "Test Picture",
        "website": "Test Website",
        "tags": ["Test", "Tag"]
    }, filters=[{
        "filterByKind": 1,
        "filterByRunOn": containerName
    }],template="""{
        "kind": {{meta.kind}},
        "created_at": {{sys.timestamp_seconds}},
        "tags": [
            ["param","run-on", """+containerName+""" ],                             
            ["param", "k", "{{in.k}}"],
            ["param", "normalize", "{{in.normalize}}"],
            {{#in.queries}}
            ["i", "{{value}}", "{{type}}", "",  "query"],
            {{/in.queries}}
            {{#in.indices}}
            ["i", "{{value}}", "{{type}}", "",  "index"],
            {{/in.indices}}
            ["expiration", "{{sys.expiration_timestamp_seconds}}"],
        ],
        "content":""
    }
    """,
    sockets={
        "in":{
            "k": {
                "type": "number",
                "description": "The number of results to return",
                "value": "1"
            },
            "normalize": {
                "type": "boolean",
                "description": "Normalize index",
                "value": "true"
            },
            "queries": {
                "type": "array",
                "description": "The queries to run",
                "schema": {
                    "value": {
                        "type": "string",
                        "description": "The query to run"
                    },
                    "type": {
                        "type": "string",
                        "description": "The type of query"
                    }
                }
            }
        },
        "out": {
            "content": {
                "type": "string",
                "description": "The content of the event"
            }
        }
    })
    print(config.getMeta())
    print(config.getFilters())
    print(config.getTemplate())


        

def __main__():
    test_nodeconfig()
    test_eventconfig()
    test_from_json()

__main__()