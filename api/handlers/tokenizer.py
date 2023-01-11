from api.decorator import lambda_api
import tiktoken

@lambda_api("tokenizer")
def tokenizer(body):
    tokenizer = tiktoken.get_encoding('gpt2')
    tokens = tokenizer.encode(body['text'])

    return (200, {"tokens": tokens})
