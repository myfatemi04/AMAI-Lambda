"""
Creates text chunks. Attempts to include as many paragraphs as possible in each chunk.
If a paragraph is longer than max_tokens, it will be split into multiple chunks.
If less than half of the maximum tokens are used, then the chunk will be split in the middle
of the current paragraph. Otherwise (if more than half of the maximum tokens are used), the
chunk will be split at the end of the most recent paragraph.
"""

# OpenAI's open-source tokenization library (as an estimate; we don't know how it works for GPT-3.)
# This can be installed with pip.
import tiktoken

encoding = tiktoken.get_encoding('gpt2')

def get_next_chunk(tokens, max_tokens, preserve_paragraphs):
    chunk = []

    # Index of the first token after the end of the paragraph
    last_paragraph_ending = 0

    for i in range(min(max_tokens, len(tokens))):
        chunk.append(tokens[i])

        # Record the most recent paragraph ending
        if encoding.decode(chunk[-2:]).endswith('\n\n'):
            last_paragraph_ending = i
    
    if preserve_paragraphs:
        if last_paragraph_ending != 0 and last_paragraph_ending >= max_tokens // 2:
            # cut off at end of most recent paragraph
            return chunk[:last_paragraph_ending + 1]
    
    return chunk

def generate_chunks(text, max_tokens, mode):
    # Split at paragraphs
    chunk = ""
    tokens = encoding.encode(text)
    while tokens:
        chunk = get_next_chunk(tokens, max_tokens, mode)
        yield encoding.decode(chunk)
        tokens = tokens[len(chunk):]

def create_text_chunks(event: dict, context):
    import json

    body = json.loads(event.get('body'))
    text = body.get('text', None)
    if text is None:
        return {"statusCode": 400, "body": {"error": "Missing required parameter 'text'"}}

    preserve_paragraphs = body.get('preserve_paragraphs', True)
    
    max_tokens = body.get('max_tokens', 2048)
    return {"result": [*generate_chunks(text, max_tokens, preserve_paragraphs)]}
