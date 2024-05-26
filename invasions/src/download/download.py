import boto3
import os
import urllib3
import json

# get bucket name of environment
s3 = boto3.client('s3')
bucket_name = os.environ.get('BUCKET_NAME')

pool_mgr = urllib3.PoolManager()


# define lambda handler that gets S3 bucket and key from event and calls import_table
def lambda_handler(event, context):

    status = 200
    headers = {
        "Content-Type": "application/json"
    }
    data = ''

    print(event)

    invasion = event["invasion"]
    filename = event["filename"]
    url = event["url"]
    target = event["folder"] + filename
    data = f'Uploaded {filename} to {target}'

    print(f'Downloading file {filename} from {url} to {target} for invasion {invasion}')

    try:
        s3.upload_fileobj(pool_mgr.request('GET', url, preload_content=False), bucket_name, target)
    except Exception as e:
        status = 400
        data = f'Error uploading {filename} to {target}: {e}'

    finally:
        return {
            "statusCode": status,
            "headers": headers,
            "body": json.dumps(data)
        }