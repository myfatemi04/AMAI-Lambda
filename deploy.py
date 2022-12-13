import datetime
import time
from api.handlers import *
import boto3
import os
from api.decorator import LambdaAPI
import lambda_uploader.package

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
    lambda_uploader.package.build_package(".", requires=['requests', 'pymongo[srv]'], zipfile_name='lambda_function.zip')

def build_if_necessary():
    if os.path.exists('lambda_function.zip'):
        mtime = _latest_mtime('api')
        zip_mtime = os.path.getmtime('lambda_function.zip')
        if zip_mtime > mtime:
            print("Package is up to date")
            return

    _build()

def deploy(fn: LambdaAPI):
    print(f"### Deploying function `{fn.name}` ###")
    
    deployed_config = lambda_client.get_function_configuration(FunctionName=fn.name)
    deployment_modified = time.mktime(time.strptime(deployed_config["LastModified"], "%Y-%m-%dT%H:%M:%S.%f%z"))
    build_modified = datetime.datetime.utcfromtimestamp(os.path.getmtime("lambda_function.zip")).timestamp()

    print(" * Checking build deploymenet")
    if build_modified < deployment_modified:
        # We don't need to update the code, the function has been "updated" somehow since we last built the package
        print(" - Function has been updated since last build, skipping code update")
    else:
        zip_content = open('lambda_function.zip', 'rb').read()
        print(" - Uploading function code [size: %d bytes]" % len(zip_content))
        lambda_client.update_function_code(FunctionName=fn.name, ZipFile=zip_content)

        print(" - Waiting before applying configuration updates")
        time.sleep(5)

    print(" * Checking environment variables")
    deployed_env = deployed_config["Environment"]["Variables"]
    env_mismatch = False
    for variable in fn.environment_variables:
        if os.environ.get(variable) != deployed_env.get(variable):
            print(f" - Environment variable update: ${variable}: {deployed_env.get(variable)} => {os.environ.get(variable)}")
            env_mismatch = True

    if env_mismatch:
        lambda_client.update_function_configuration(FunctionName=fn.name, Environment={"Variables": {
            variable: os.environ[variable] for variable in fn.environment_variables
        }})
        print(" - Updated environment variables")
    else:
        print(" - No environment variable updates needed")

    print(" * Checking handler")
    if deployed_config["Handler"] != f"api.handlers.{fn.name}":
        lambda_client.update_function_configuration(FunctionName=fn.name, Handler=f"api.handlers.{fn.name}")
        print(" - Updated handler")
    else:
        print(" - No handler updates needed")

build_if_necessary()
# deploy(retrieval_enhancement)
# deploy(oauth)
deploy(generate_for_prompt)
# deploy(my_info)
# deploy(generate_completion)
