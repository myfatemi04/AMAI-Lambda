import boto3

s3 = boto3.resource('s3')

def save_to_s3(bucket_name, file_name, file_content):
    s3.Bucket(bucket_name).put_object(Key=file_name, Body=file_content)
