import datetime
import os
import time

import api.handlers
import boto3
import lambda_uploader.package
from api.decorator import LambdaAPI

lambda_client = boto3.client('lambda')

def _latest_mtime(folder):
    # use os.walk
    mtime = 0
    for root, dirs, files in os.walk(folder):
        for file in files:
            mtime = max(mtime, os.path.getmtime(os.path.join(root, file)))
    return mtime

def _build():
    try:
        os.unlink('lambda_function.zip')
    except FileNotFoundError:
        pass

    print("Building package...")
    lambda_uploader.package.build_package(".", requires=['requests', 'pymongo[srv]', 'pdfminer.six', 'ftfy', 'youtube-transcript-api'], zipfile_name='lambda_function.zip')

def build_if_necessary():
    if os.path.exists('lambda_function.zip'):
        mtime = _latest_mtime('api')
        zip_mtime = os.path.getmtime('lambda_function.zip')
        if zip_mtime > mtime:
            print("Package is up to date")
            return

    _build()

def deploy(fn: LambdaAPI, force_deploy=False):
    print(f"### Deploying function `{fn.name}` ###")
    
    deployed_config = lambda_client.get_function_configuration(FunctionName=fn.name)
    deployment_modified = time.mktime(time.strptime(deployed_config["LastModified"], "%Y-%m-%dT%H:%M:%S.%f%z"))
    build_modified = datetime.datetime.utcfromtimestamp(os.path.getmtime("lambda_function.zip")).timestamp()

    print(" * Checking build deployment")
    if build_modified < deployment_modified and not force_deploy:
        # We don't need to update the code, the function has been "updated" somehow since we last built the package
        print(" - Function has been updated since last build, skipping code update")
    else:
        zip_content = open('lambda_function.zip', 'rb').read()
        print(" - Uploading function code [size: %d bytes]" % len(zip_content))
        lambda_client.update_function_code(FunctionName=fn.name, ZipFile=zip_content)

        print(" - Waiting before applying configuration updates")
        time.sleep(1)

    print(" * Checking environment variables")
    deployed_env = deployed_config.get("Environment", {}).get("Variables", {})
    env_updates = {}
    for variable in fn.environment_variables:
        # allows for custom environment variables
        if '=' in variable:
            variable_name, variable_value = variable.split('=', 1)
        else:
            variable_name = variable
            variable_value = os.environ.get(variable)
        if variable_value != deployed_env.get(variable_name):
            print(f" - Environment variable update: ${variable_name}: {deployed_env.get(variable_name)} => {variable_value}")
            env_updates[variable_name] = variable_value

    if len(env_updates) > 0:
        lambda_client.update_function_configuration(FunctionName=fn.name, Environment={"Variables": {**deployed_env, **env_updates}})
        print(" - Updated environment variables")
        time.sleep(1)
    else:
        print(" - No environment variable updates needed")

    print(" * Checking handler")
    if deployed_config["Handler"] != f"api.handlers.{fn.name}.{fn.name}":
        lambda_client.update_function_configuration(FunctionName=fn.name, Handler=f"api.handlers.{fn.name}")
        print(" - Updated handler")
        time.sleep(1)
    else:
        print(" - No handler updates needed")

if __name__ == '__main__':
    import re
    import sys
    import importlib

    if len(sys.argv) != 2:
        print("Usage: python deploy.py <function_name>")
        sys.exit(1)

    if not re.match(r'^[a-z0-9_]+$', sys.argv[1]):
        print("Invalid function name. Function names must be lowercase, and can only contain letters, numbers, and underscores.")
        sys.exit(1)

    build_if_necessary()

    fn = getattr(importlib.import_module('api.handlers.' + sys.argv[1]), sys.argv[1])
    
    deploy(fn, force_deploy=True)
