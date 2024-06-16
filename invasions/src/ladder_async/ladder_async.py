import json
import urllib
from irus import IrusResources, IrusMemberList, IrusLadder, IrusInvasion
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = IrusResources.logger()
textract = IrusResources.textract()
table = IrusResources.table()

# define lambda handler that gets S3 bucket and key from event and calls import_table
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event:dict, context:LambdaContext):

    status = 200
    headers = {
        "Content-Type": "application/json"
    }
    msg = ''

    # get bucket and key from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    # key = event['Records'][0]['s3']['object']['key']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    folders = key.split('/')

    if len(folders) != 3:
        status = 401
        msg = f'Skipping {key} as it is not in the correct format'
    elif folders[0] != 'ladders':
        status = 401
        msg = f'Skipping {key} as it is not in the correct format'
    elif key[-4:] != '.png':
        status = 401
        msg = f'Skipping {key} as it is not a PNG file'
    else:
        try:
            name = folders[1]
            logger.info(f'ladders: {bucket}/{key} for {name}')
            members = IrusMemberList()
            invasion = IrusInvasion.from_table(name)
            ladder = IrusLadder.from_ladder_image(invasion, members, bucket, key)
            msg = str(ladder)
        except Exception as e:
            status = 500
            msg = f'Error importing {key} for {invasion}: {e}'


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
