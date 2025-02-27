from fastapi import FastAPI
import uuid
import time
import random
import re

from text_generation import gen_paragraph
from api import ChatCompletionsRequest, CompletionsRequest

app = FastAPI()


@app.post("/v1/chat/completions")
def chat_completions(request: ChatCompletionsRequest):
    choices = []
    for i in range(request.n):
        generated_text, hit_max_length = gen_paragraph(max_len=request.max_tokens)

        if request.logprobs:
            logprobs = {"content": []}
            for word in generated_text.split():
                logprobs["content"].append(
                    {"token": word,
                     "logprob": -random.random(),
                     "bytes": [],
                     "top_logprobs": [],
                     })
        else:
            logprobs = None
        choices.append({
            "index": i,
            "message": {"role": "assistant", "content": generated_text, "refusal": None},
            "logprobs": logprobs,
            "finish_reason": "stop" if not hit_max_length else "length",
        })

    return {
        "id": "chat_completion_" + uuid.uuid4().hex,
        "object": "chat.completion",
        "created": time.time(),
        "model": request.model,
        "system_fingerprint": uuid.uuid4().hex,
        "choices": choices,
        "usage": {
        }
    }


@app.post("/v1/completions")
def completions(request: CompletionsRequest):
    choices = []
    for i in range(request.n):
        if request.echo:
            generated_text, hit_max_length = gen_paragraph(max_len=request.max_tokens)
            generated_text = request.prompt + generated_text
        else:
            generated_text, hit_max_length = gen_paragraph(max_len=request.max_tokens)

        if request.logprobs:
            tokens = re.split(r'(\s+)', generated_text)
            offset = 0

            word_offsets = []
            token_logprobs = []
            top_logprobs = []
            for token in tokens:
                word_offsets.append(offset)
                offset += len(token)
                lp = -random.random()
                token_logprobs.append(lp)
                top_logprobs.append({token: lp})
            logprobs = {
                "text_offset": word_offsets,
                "token_logprobs": token_logprobs,
                "tokens": tokens,
                "top_logprobs": top_logprobs,
            }
        else:
            logprobs = None

        choices.append({
            "index": i,
            "text": generated_text,
            "logprobs": logprobs,
            "finish_reason": "stop" if not hit_max_length else "length",
        })

    return {
        "id": "chat_completion_" + uuid.uuid4().hex,
        "object": "chat.completion",
        "created": time.time(),
        "model": request.model,
        "system_fingerprint": uuid.uuid4().hex,
        "choices": choices,
        "usage": {}
    }
