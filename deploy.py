import datetime
import time
from api.handlers import *
import boto3
import os
from api.decorator import LambdaAPI
import lambda_uploader.package

lambda_client = boto3.client('lambda')

def build():
    try:
        os.unlink('lambda_function.zip')
    except FileNotFoundError:
        pass

    print("Building package...")
    lambda_uploader.package.build_package(".", requires=['requests', 'pymongo[srv]'], zipfile_name='lambda_function.zip')

def deploy(fn: LambdaAPI):
    live_config = lambda_client.get_function_configuration(FunctionName=fn.name)
    last_modified_str = live_config["LastModified"]
    last_modified = time.mktime(time.strptime(last_modified_str, "%Y-%m-%dT%H:%M:%S.%f%z"))

    print("Function was last modified", last_modified)
    print("lambda_function.zip was last modified", os.path.getmtime("lambda_function.zip"))

    if os.path.getmtime("lambda_function.zip") < last_modified:
        # We don't need to update the code, the function has been "updated" somehow since we last built the package
        print("Function has been updated since last build, skipping code update")
    else:
        zip_content = open('lambda_function.zip', 'rb').read()
        print("Uploading function code [size: %d bytes]" % len(zip_content))
        lambda_client.update_function_code(FunctionName=fn.name, ZipFile=zip_content)

        print("Waiting before applying configuration updates")
        time.sleep(5)

    live_env_variables = live_config["Environment"]["Variables"]
    has_mismatched_variable = False
    for variable in fn.environment_variables:
        if os.environ.get(variable) != live_env_variables.get(variable):
            print(f"Environment variable update: ${variable}: {live_env_variables.get(variable)} => {os.environ.get(variable)}")
            has_mismatched_variable = True

    if has_mismatched_variable:
        lambda_client.update_function_configuration(FunctionName=fn.name, Environment={"Variables": {
            variable: os.environ[variable] for variable in fn.environment_variables
        }})
        print("Updated environment variables")
    else:
        print("No environment variable updates needed")

    if live_config["Handler"] != f"api.handlers.{fn.name}":
        lambda_client.update_function_configuration(FunctionName=fn.name, Handler=f"api.handlers.{fn.name}")
        print("Updated handler")
    else:
        print("No handler updates needed")

functions = [
    oauth,
    my_info
]

build()
deploy(retrieval_enhancement)
# deploy(oauth)
# deploy(generate_for_prompt)
# deploy(my_info)
# deploy(generate_completion)
