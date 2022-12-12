import traceback
import requests
import json
import os
import time
import bson
from db import users, oauth_tokens

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
    expires_in = result.json()['expires_in']
    refresh_token = result.json()['refresh_token']
    scope = result.json()['scope']

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
    user_id = user['_id']

    result = oauth_tokens.insert_one({
        "user_id": user_id,
        "provider": "google",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "valid_until": time.time() + expires_in,
        "scope": scope,
    })
    oauth_token_id = result.inserted_id
    
    return r(200, {"access_token": oauth_token_id})

def refresh_google_token(token):
    token_uri = "https://oauth2.googleapis.com/token"
    client_id = os.environ['GOOGLE_CLIENT_ID']
    client_secret = os.environ['GOOGLE_CLIENT_SECRET']
    grant_type = "refresh_token"
    refresh_token = token['refresh_token']

    result = requests.post(token_uri, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": grant_type,
        "refresh_token": refresh_token
    })
    if result.status_code != 200:
        return r(result.status_code, {"error": result.text})

    access_token = result.json()['access_token']
    expires_in = result.json()['expires_in']
    refresh_token = result.json()['refresh_token']

    oauth_tokens.update_one({
        "_id": bson.ObjectId(token['_id'])
    }, {
        "$set": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "valid_until": time.time() + expires_in,
        },
    })


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
    
    oauth_token = oauth_tokens.find_one({"_id": bson.ObjectId(access_token)})

    if oauth_token is None:
        return r(400, {"error": "access_token is invalid"})

    if oauth_token['valid_until'] < time.time():
        # Try to refresh the token
        try:
            refresh_google_token(oauth_token)
        except Exception as e:
            traceback.print_exc()
            return r(400, {"error": "Could not refresh token"})

    user = users.find_one({"_id": bson.ObjectId(oauth_token['user_id'])})
    if user is None:
        return r(400, {"error": "User not found"})
    
    return r(200, {
        "_id": str(user['_id']),
        "email": user['email'],
        "name": user['name'],
        "profile_photo": user['profile_photo'],
    })
