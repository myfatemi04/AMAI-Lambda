import time

from api.db import embeddings_usage
from api.decorator import lambda_api
from api.errors import missing_from_request
from api.llms import openai_embeddings


@lambda_api("generate_embedding", ["MONGO_URI", "OPENAI_API_KEY"], require_auth=True)
def generate_embedding(body, user):
    prompt = body.get("prompt")

    if prompt is None:
        return missing_from_request("prompt")

    embedding = openai_embeddings(prompt)

    embeddings_usage.insert_one({
        "user_id": user["_id"],
        "prompt": prompt,
        "embedding": embedding,
        "backend": "openai:text-embedding-ada-002",
        "timestamp": time.time(),
    })

    return (200, {"embedding": embedding})
