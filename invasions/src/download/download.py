import urllib3
import json
from irus import IrusResources
from aws_lambda_powertools.utilities.typing import LambdaContext

resources = IrusResources()
logger = resources.logger
s3 = resources.s3
bucket_name = resources.bucket_name

pool_mgr = urllib3.PoolManager()


# define lambda handler that gets S3 bucket and key from event and calls import_table
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):

    status = 200
    headers = {
        "Content-Type": "application/json"
    }
    data = ''

    invasion = event["invasion"]
    filename = event["filename"]
    url = event["url"]
    target = event["folder"] + filename
    data = f'Downloaded {filename} to {event["folder"]}'

    logger.info(f'Downloading file {filename} from {url} to {target} for invasion {invasion}')

    try:
        if filename[-4:] != '.png':
            status = 400
            logger.warning(f'Skipping {filename} as it is not a PNG file')
            msg = f'Skipping {filename} as it is not a PNG file'
        else:
            s3.upload_fileobj(pool_mgr.request('GET', url, preload_content=False), bucket_name, target)
        
    except Exception as e:
        status = 400
        logger.error(f'Error downloading {filename} to {target}: {e}')
        data = f'Error downloading {filename} to {target}: {e}'

    finally:
        return {
            "statusCode": status,
            "headers": headers,
            "body": json.dumps(data)
        }