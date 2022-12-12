import requests
import json
import os

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
    
    token_uri = "https://oauth2.googleapis.com/token"
    code = body['code']
    client_id = os.environ['GOOGLE_CLIENT_ID']
    client_secret = os.environ['GOOGLE_CLIENT_SECRET']
    grant_type = "authorization_code"
    redirect_uri = "https://augmateai.michaelfatemi.com/google-callback"

    result = requests.post(token_uri, data={
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": grant_type,
        "redirect_uri": redirect_uri
    })
    if result.status_code != 200:
        return r(result.status_code, {"error": result.text})
    return r(200, result.json())
