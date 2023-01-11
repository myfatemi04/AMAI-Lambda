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
    def __init__(self, function, name, environment_variables, require_auth):
        self.fn = function
        self.name = name
        self.environment_variables = environment_variables
        self.require_auth = require_auth
        if self.require_auth and "MONGO_URI" not in self.environment_variables:
            self.environment_variables.append("MONGO_URI")
            print("WARNING: MONGO_URI is required for authentication, but was not specified in environment_variables. Adding it automatically.")

    def __call__(self, event, context):
        import api.db
        import bson

        try:
            try:
                body = json.loads(event['body'])
            except Exception as e:
                return create_response(400, {"error": "Could not parse body as JSON"})

            if self.require_auth:
                print(event['headers'])
                if 'authorization' not in event['headers']:
                    return create_response(401, {"error": "No Authorization header"})
                token = event['headers']['authorization'][len("Bearer "):]

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
            return create_response(500, {"error": "Internal server error"})

def lambda_api(function_name, environment_variables=[], require_auth=False):
    def wrapper(fn):
        return LambdaAPI(fn, function_name, environment_variables, require_auth)
    return wrapper
