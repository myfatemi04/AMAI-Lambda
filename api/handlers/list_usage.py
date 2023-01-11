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

    return event_counts

def find(collection, max_objectid, user):
    import bson

    query = {'user_id': user['_id']}
    if max_objectid:
        query['_id'] = {'$lt': bson.ObjectId(max_objectid)}

    return collection.find(query).sort('_id', -1).limit(128)

@api.decorator.lambda_api('list_usage', ['MONGO_URI'], require_auth=True)
def list_usage(body: dict, user: dict):
    import bson
    import api.errors

    if 'collection' not in body:
        return api.errors.missing_from_request('collection')

    col = body['collection']
    if col not in {'prompt_usage', 'retrieval_enhancement_usage', 'embeddings_usage'}:
        return 400, {"error": "collection name is invalid"}

    max_objectid = body.get('max_objectid', None)
    
    import tiktoken

    gpt2_tokenizer = tiktoken.get_encoding('gpt2')
    
    if col == 'prompt_usage':

        results = [
            {
                '_id': str(result['_id']),
                'input_token_count': len(gpt2_tokenizer.encode(result['prompt_template'].format(**result['variables']))),
                'output_token_count': len(gpt2_tokenizer.encode(result['completion'])),
            }
            for result in find(api.db.prompt_usage, max_objectid, user)
        ]
    elif col == 'retrieval_enhancement_usage':
        results = [
            {
                '_id': str(result['_id']),
                'query': result['query'],
                'backend': result['backend'],
            }
            for result in find(api.db.retrieval_enhancement_usage, max_objectid, user)
        ]
    elif col == 'embeddings_usage':
        results = [
            {
                '_id': str(result['_id']),
                'token_count': len(gpt2_tokenizer.encode(result['prompt'])),
            }
            for result in find(api.db.embeddings_usage, max_objectid, user)
        ]
    else:
        return 400, "invalid collection name"
    
    return 200, results
