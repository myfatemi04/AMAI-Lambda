#!/bin/sh

cd $1

rm lambda_function.zip

lambda-uploader --no-upload

aws lambda update-function-code --function-name $1 --zip-file fileb://$(pwd)/lambda_function.zip
aws lambda update-function-configuration --function-name $1 --environment \
 "Variables={OPENAI_API_KEY=$OPENAI_API_KEY,MONGO_URI=$MONGO_URI,HUGGINGFACE_API_KEY=$HUGGINGFACE_API_KEY},BING_SEARCH_V7_SUBSCRIPTION_KEY1=$BING_SEARCH_V7_SUBSCRIPTION_KEY1"

cd -
