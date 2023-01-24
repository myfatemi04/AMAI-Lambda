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
    result = create_prompt(
        template='''Text:\n"""\n{context}\n"""\n\nInstructions:\n{instructions}\n\nAnswer:\n''',
        variables=[{"name": "context"}, {"name": "instructions"}],
        user_id=bson.ObjectId("63bf39f45117bd92a289699f"),
        generation_params={"max_tokens": 256},
        name="default_generator"
    )
    print(result)

# _create_prompts()
