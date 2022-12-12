import traceback
import requests
import json
import os
import time
import bson
from db import users, access_tokens

def r(code, body):
	print("Response {} with body {}".format(code, json.dumps(body)))
	return {
		'statusCode': code,
		'body': json.dumps(body),
		'headers': {
			'Access-Control-Allow-Origin': '*',
		}
	}

def google_handler(event, context):
    if 'body' not in event:
        return r(400, {"error": "No body in event"})

    try:
        body = json.loads(event['body'])
    except:
        return r(400, {"error": "Could not parse body as JSON"})

    if 'code' not in body:
        return r(400, {"error": "No code in body"})
    
    code = body['code']
    if type(code) is not str:
        return r(400, {"error": "Code is not a string"})
    
    if 'host' not in body:
        return r(400, {"error": "No host in body"})

    host = body['host']
    if type(host) is not str:
        return r(400, {"error": "Host is not a string"})
    
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
        return r(result.status_code, {"error": result.text, "stage": "get_access_token"})

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
        return r(user_info_request.status_code, {"error": user_info_request.text, "stage": "get_user_info"})
    
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

    return r(200, {"access_token": str(insertion.inserted_id)})

def my_info_handler(event, context):
    if 'body' not in event:
        return r(400, {"error": "No body in event"})

    try:
        body = json.loads(event['body'])
    except:
        return r(400, {"error": "Could not parse body as JSON"})

    if 'access_token' not in body:
        return r(400, {"error": "No access_token in body"})
    
    access_token = body['access_token']
    if type(access_token) is not str:
        return r(400, {"error": "access_token is not a string"})
    
    access_token = access_tokens.find_one({"_id": bson.ObjectId(access_token)})

    if access_token is None:
        return r(400, {"error": "access_token is not found"})

    if access_token['valid_until'] < time.time():
        access_tokens.delete_one({"_id": access_token['_id']})
        return r(400, {"error": "access_token is expired"})

    user = users.find_one({"_id": bson.ObjectId(access_token['user_id'])})
    if user is None:
        return r(400, {"error": "User not found"})
    
    return r(200, {
        "_id": str(user['_id']),
        "email": user['email'],
        "name": user['name'],
        "profile_photo": user['profile_photo'],
    })
