import json
import urllib
from irus import IrusResources, IrusMemberList, IrusLadder, IrusInvasion
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = IrusResources.logger()
bucket_name = IrusResources.bucket_name()

# define lambda handler that gets S3 bucket and key from event and calls import_table
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event:dict, context:LambdaContext):

    status = 200
    headers = {
        "Content-Type": "application/json"
    }
    msg = ''

    name = event["invasion"]
    filename = event["filename"]
    folder = event["folder"]

    try:
        members = IrusMemberList()
        invasion = IrusInvasion.from_table(name)
        ladder = IrusLadder.from_image(invasion, members, bucket_name, folder + filename)
        msg = str(ladder)
    except Exception as e:
        status = 500
        msg = f'Error importing ladder {filename} for {invasion}: {e}'

    if status == 200:
        logger.info(msg)
    elif status == 401:
        logger.warning(msg)
    else:
        logger.error(msg)

    return {
        "statusCode": status,
        "headers": headers,
        "body": json.dumps(msg)
    }
