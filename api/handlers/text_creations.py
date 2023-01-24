from api.decorator import lambda_api
import api.db
import api.errors
import time

@lambda_api("text_creations", ["MONGO_URI"], require_auth=True)
def text_creations(body, user):
    request_type = body.pop("request_type")

    if request_type == "create":
        return create_text_creation(body, user)
    elif request_type == "update":
        return update_text_creation(body, user)
    elif request_type == "list":
        return list_text_creations(body, user)
    
    return (400, {"error": "invalid request_type"})


def create_text_creation(body, user):
    user_id = user['_id']
    title = body.get("title")

    if title is None:
        return api.errors.missing_from_request("missing title")
    
    text_creation = api.db.text_creations.insert_one({
        "user_id": user_id,
        "title": title,
        "timestamp": time.time(),
        "last_checkpoint_timestamp": -1.0,
        "last_modified_timestamp": time.time(),
    })

    return (200, {"inserted_id": text_creation.inserted_id})

def update_text_creation(body, user):
    text = body.get("text")
    title = body.get("title")
    text_creation_id = body.get("text_creation_id")
    if text_creation_id is None:
        return api.errors.missing_from_request("text or text_creation_id")

    text_creation = api.db.text_creations.find_one({"_id": text_creation_id, "user_id": user['_id']})
    if text_creation is None:
        return api.errors.not_found("text_creation")

    updates = {}
    if text is not None:
        updates["text"] = text
    if title is not None:
        updates["title"] = title
    updates["last_modified_timestamp"] = time.time()
    
    api.db.text_creations.update_one({"_id": text_creation_id}, {"$set": updates})

    return (200, {"updated": True})

def list_text_creations(body, user):
    user_id = user['_id']
    text_creations = api.db.text_creations.find({"user_id": user_id}).sort("timestamp", -1)
    return (200, {"text_creations": list(text_creations)})
