import asyncio
import json

from duckduckgo_search import DDGS
import python_weather


function_registry = {}

def ToolFunName(name):
    def decorator(func):
        if name in function_registry:
            raise ValueError(f"Function name '{name}' is already registered.")
        function_registry[name] = func
        return func
    return decorator


async def handle_tool_calls(tool_calls):
    tool_outputs = []

    for tool in tool_calls:
        output = await call_tool_function(tool)
        tool_outputs.append(output)
    print(f"Tool call: {tool_calls}")
    return tool_outputs

# async def handle_tool_calls(tool_calls):
#     tasks = []
#     print(f"Tool call: {tool_calls}")
#     for tool in tool_calls:
#         task = call_tool_function(tool)
#         tasks.append(task)
    
#     # 平行執行所有的函式呼叫
#     results = await asyncio.gather(*tasks)
#     print(f"Tool call results: {results}")
#     return results

async def call_tool_function(tool_call):
    func = function_registry.get(tool_call.function.name)
    if func:
        return await func(tool_call)
    else:
        raise ValueError(f"Function {tool_call} not found")

@ToolFunName("web_search")    
async def web_search(tool_call):
    print(f"web_search: {tool_call}")
    params = json.loads(tool_call.function.arguments)
    """
        keywords: str,
        region: str = "wt-wt",
        safesearch: str = "moderate",
        timelimit: str | None = None,
        backend: str = "api",
        max_results: int | None = None,
    """
    print(f"web_search: {params}")
    results = DDGS().text(params["keywords"]
                        , region=params.get("region", "wt-wt")
                        , safesearch='off'
                        , timelimit=None
                        , backend="api"
                        , max_results=20)
    
    return {
        "tool_call_id": tool_call.id,
        "output": json.dumps(results)
    }