from ..decorator import lambda_api


@lambda_api("my_info", environment_variables=["MONGO_URI"], require_auth=True)
def my_info(body, user):
    return (200, {
        "_id": str(user['_id']),
        "email": user['email'],
        "name": user['name'],
        "profile_photo": user['profile_photo'],
    })
