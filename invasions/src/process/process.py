import urllib3
import json
from irus import IrusResources, IrusMemberList, IrusLadder, IrusInvasion
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = IrusResources.logger()
s3 = IrusResources.s3()
bucket_name = IrusResources.bucket_name()

pool_mgr = urllib3.PoolManager()

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):

    status = 200
    headers = {
        "Content-Type": "application/json"
    }
    data = ''

    name = event["invasion"]
    filename = event["filename"]
    url = event["url"]
    target = event["folder"] + filename
    process = event["process"]
    data = f'Downloaded and processed {filename} for invasion {name}'

    logger.info(f'Downloading file {filename} from {url} to {target} for invasion {name}')

    try:
        if filename[-4:] != '.png':
            status = 400
            logger.warning(f'Skipping {filename} as it is not a PNG file')
            data = f'Skipping {filename} as it is not a PNG file'
        else:
            s3.upload_fileobj(pool_mgr.request('GET', url, preload_content=False), bucket_name, target)
        
    except Exception as e:
        status = 400
        logger.error(f'Error downloading {filename} to {target}: {e}')
        data = f'Error downloading {filename} to {target}: {e}'

    try:
        if status == 200:
            logger.info(f'Processing {process} image {filename} for invasion {name}')
            members = IrusMemberList()
            invasion = IrusInvasion.from_table(name)
            ladder = None
            if process == 'ladder':
                ladder = IrusLadder.from_ladder_image(invasion, members, bucket_name, target)
            else:
                ladder = IrusLadder.from_roster_image(invasion, members, bucket_name, target)
            data = f'Successful download of {filename}. ' + ladder.str()

    except Exception as e:
        status = 400
        data = f'Error importing ladder {filename} for {invasion}: {e}'

    if status == 200:
        logger.info(data)
    else:
        logger.warning(data)

    return {
        "statusCode": status,
        "headers": headers,
        "body": json.dumps(data)
    }