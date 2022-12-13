import requests
import os
import time
from api.db import users, access_tokens
from api.decorator import lambda_api

@lambda_api("oauth", environment_variables=['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'MONGO_URI'])
def google_handler(body):
    if 'code' not in body:
        return (400, {"error": "No code in body"})
    
    code = body['code']
    if type(code) is not str:
        return (400, {"error": "Code is not a string"})
    
    if 'host' not in body:
        return (400, {"error": "No host in body"})

    host = body['host']
    if type(host) is not str:
        return (400, {"error": "Host is not a string"})
    
    token_uri = "https://oauth2.googleapis.com/token"
    code = body['code']
    host = body['host']
    client_id = os.environ['GOOGLE_CLIENT_ID']
    client_secret = os.environ['GOOGLE_CLIENT_SECRET']
    grant_type = "authorization_code"
    if host == 'localhost':
        redirect_uri = 'http://localhost:3000/google-callback'
    else:
        redirect_uri = f"https://{host}/google-callback"

    result = requests.post(token_uri, data={
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": grant_type,
        "redirect_uri": redirect_uri
    })
    if result.status_code != 200:
        return (result.status_code, {"error": result.text, "stage": "get_access_token"})

    access_token = result.json()['access_token']
    # expires_in = result.json()['expires_in']
    # # not provided after the first call
    # refresh_token = result.json().get('refresh_token', None)
    # scope = result.json()['scope']

    user_info_uri = "https://www.googleapis.com/oauth2/v1/userinfo"
    user_info_request = requests.get(user_info_uri, headers={
        "Authorization": "Bearer {}".format(access_token)
    })
    if user_info_request.status_code != 200:
        return (user_info_request.status_code, {"error": user_info_request.text, "stage": "get_user_info"})
    
    user_info = user_info_request.json()

    users.update_one({
        "email": user_info['email'],
    }, {
        "$set": {
            "email": user_info['email'],
            "name": user_info['name'],
            'profile_photo': user_info['picture'],
        },
    }, upsert=True)

    user = users.find_one({"email": user_info['email']})
    insertion = access_tokens.insert_one({"user_id": user['_id'], "valid_until": time.time() + 3600 * 24 * 30})

    return (200, {"access_token": str(insertion.inserted_id)})
