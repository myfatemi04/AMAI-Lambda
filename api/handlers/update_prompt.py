import api.db
import api.decorator
import api.errors
import bson

@api.decorator.lambda_api("update_prompt", environment_variables=["MONGO_URI"], require_auth=True)
def update_prompt(body, user):
    prompt_id = body.get("prompt_id", None)
    if prompt_id is None:
        return api.errors.missing_from_request("missing prompt_id")
    
    new_name = body.get("new_name", None)
    if new_name is None:
        return api.errors.missing_from_request("missing new_name")

    result = api.db.prompts.update_one({"_id": bson.ObjectId(prompt_id), "user_id": user["_id"]}, {"$set": {"name": new_name}})
    if result.matched_count == 0:
        return api.errors.not_found("prompt with id prompt_id and accessible by user")
    
    return 200, {"changed": result.modified_count != 0}
