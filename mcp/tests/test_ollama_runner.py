import json

from eh_mcp.ollama_runner import _arguments, _schema, _tool_result


class Tool:
    name = "where_am_i"
    description = "Return saved progress."
    inputSchema = {"type": "object", "properties": {"focus": {"type": "string"}}}


class Text:
    def __init__(self, text):
        self.text = text


class Result:
    content = [Text('{"current": "probability"}')]


def test_mcp_tool_becomes_an_ollama_function():
    tool = _schema(Tool())
    assert tool["function"]["name"] == "where_am_i"
    assert tool["function"]["parameters"]["properties"]["focus"]["type"] == "string"


def test_tool_arguments_accept_json_or_objects():
    assert _arguments('{"focus":"probability"}') == {"focus": "probability"}
    assert _arguments({"focus": "ranking"}) == {"focus": "ranking"}


def test_tool_result_preserves_structured_json():
    assert json.loads(_tool_result(Result())) == {"current": "probability"}
