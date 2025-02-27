from typing import Union, List
from pydantic import BaseModel


class BaseCompletionsRequest(BaseModel):
    model: str
    max_tokens: int = None
    n: int = 1
    logprobs: bool = False


class ChatCompletionsRequest(BaseCompletionsRequest):
    messages: List


class CompletionsRequest(BaseCompletionsRequest):
    prompt: Union[str, List[str]]
    echo: bool = False