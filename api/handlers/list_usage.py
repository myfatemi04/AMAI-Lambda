import api.decorator
import api.db

def get_event_counts(user):
    import tiktoken

    gpt2_tokenizer = tiktoken.get_encoding('gpt2')

    uid = user['_id']

    event_counts = {
        'search': 0,
        'upload': 0,
        'embedding_tokens': 0,
        'completion_input_tokens': 0,
        'completion_output_tokens': 0,
    }

    for retrieval_enhancement_event in api.db.retrieval_enhancement_usage.find({"user_id": uid}):
        if retrieval_enhancement_event['backend'] == 'bing':
            event_counts['search'] += 1
        elif retrieval_enhancement_event['backend'] in {'proxy', 'youtube'}:
            event_counts['upload'] += 1
        else:
            print('Unknown backend:', retrieval_enhancement_event['backend'])
            event_counts['upload'] += 1

    for completion_event in api.db.prompt_usage.find({"user_id": uid}):
        prompt_template = completion_event['prompt_template']
        completion = completion_event['completion']
        variables = completion_event['variables']
        event_counts['completion_input_tokens'] += len(gpt2_tokenizer.encode(prompt_template.format(**variables)))
        event_counts['completion_output_tokens'] += len(gpt2_tokenizer.encode(completion))

    for embedding_event in api.db.embeddings_usage.find({"user_id": uid}):
        event_counts['embedding_tokens'] += len(gpt2_tokenizer.encode(embedding_event['prompt']))

@api.decorator.lambda_api('list_usage', ['MONGO_URI'], require_auth=True)
def list_usage(body, user):
    return 200, get_event_counts(user)
