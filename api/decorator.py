import json
import time
import traceback

def create_response(status_code, body):
    return {
		'statusCode': status_code,
		'body': json.dumps(body),
		'headers': {
			'Access-Control-Allow-Origin': '*',
		}
	}

# Decorator
class LambdaAPI:
    def __init__(self, function, name, environment_variables, require_auth, use_raw):
        self.fn = function
        self.name = name
        self.environment_variables = environment_variables
        self.require_auth = require_auth
        self.use_raw = use_raw
        if self.require_auth and "MONGO_URI" not in self.environment_variables:
            self.environment_variables.append("MONGO_URI")
            print("WARNING: MONGO_URI is required for authentication, but was not specified in environment_variables. Adding it automatically.")

    def __call__(self, event, context):
        try:
            if self.use_raw:
                return create_response(*self.fn(event))

            try:
                body = json.loads(event['body'])
            except Exception as e:
                return create_response(400, {"error": "Could not parse body as JSON"})

            if self.require_auth:
                import api.db
                import bson
                
                if 'authorization' not in event['headers']:
                    return create_response(401, {"error": "No Authorization header"})
                token = event['headers']['authorization'][len("Bearer "):]

                if type(token) != str or len(token) != 24:
                    return create_response(401, {"error": "Invalid access token"})

                access_token = api.db.access_tokens.find_one({"_id": bson.ObjectId(token)})
                if access_token is None:
                    return create_response(401, {"error": "Invalid access token"})

                if access_token['valid_until'] < time.time():
                    api.db.access_tokens.delete_one({"_id": access_token['_id']})
                    return (401, {"error": "Access token expired"})

                user = api.db.users.find_one({"_id": access_token['user_id']})
                if user is None:
                    return create_response(401, {"error": "Invalid access token"})

                status_code, response = self.fn(body, user)
            else:
                status_code, response = self.fn(body)

            return create_response(status_code, response)
        except Exception as e:
            traceback.print_exc()
            traceback.format_exc()
            return create_response(500, {"error": "Internal server error. Trace: " + traceback.format_exception(limit=3)})

def lambda_api(function_name, environment_variables=[], require_auth=False, use_raw=False):
    def wrapper(fn):
        return LambdaAPI(fn, function_name, environment_variables, require_auth, use_raw)
    return wrapper
