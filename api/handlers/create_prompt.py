import api.db
import bson

def create_prompt(template: str, variables: list, user_id: bson.ObjectId, generation_params: dict, name: str):
    """
    General format:
    {
        "_id" : ObjectId(...),
        "template" : "Instruction: {question}\n\n<...>",
        "variables" : [
            { "name" : "question" },
            ...
        ],
        "user_id" : ObjectId(...),
        "generation_params" : {
            "max_tokens" : 400
        },
        "name" : "compile_answers_youtube"
    }
    """
    result = api.db.prompts.insert_one({
        "template": template,
        "variables": variables,
        "user_id": user_id,
        "generation_params": generation_params,
        "name": name,
    })
    return result.inserted_id

def _create_prompts():
    create_prompt(
        "{context}",
        [{"name": "context"}],
        bson.ObjectId("63bf39f45117bd92a289699f"),
        {"max_tokens": 256},
        "default_generator"
    )
