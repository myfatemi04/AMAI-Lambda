#!/bin/sh

cd $1

rm lambda_function.zip

lambda-uploader --no-upload

cd -
