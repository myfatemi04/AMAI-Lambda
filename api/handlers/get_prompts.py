import api.db
import api.decorator
import bson

@api.decorator.lambda_api("get_prompts", environment_variables=["MONGO_URI"], require_auth=True)
def get_prompts(body, user):
    prompts = list(api.db.prompts.find({"user_id": user._id}))
    for prompt in prompts:
        for key in prompt:
            if isinstance(prompt[key], bson.ObjectId):
                prompt[key] = str(prompt[key])
    
    return 200, prompts
