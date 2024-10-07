import json
from irus import IrusResources, IrusLadder, IrusInvasion, IrusReport
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = IrusResources.logger()

# define lambda handler that gets S3 bucket and key from event and calls import_table
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event:dict, context:LambdaContext):

    status = 200
    headers = {
        "Content-Type": "application/json"
    }
    body = {
        'template': '''
        # Report for Invasion {}
        Ranks: {}
        Members ({}): {}
        Non Members: {}
        Contiguous: {}
        {}
        ''',
        'name': 'TBD',
        'ranks': '0',
        'members': '0',
        'memberlist': 'TBD',
        'nonmemberlist': 'TBD',
        'contiguous': '0',
        'url': 'TBD'
    }

    name = event["invasion"]

    try:
        invasion = IrusInvasion.from_table(name)
        ladder = IrusLadder.from_invasion(invasion)
        body['name'] = name
        body['ranks'] = ladder.count()
        body['members'] = ladder.members()
        body['memberlist'] = ladder.list(member = True)
        body['nonmemberlist'] = ladder.list(member = False)
        contiguous = ladder.contiguous_from_1_until()
        if contiguous != ladder.count():
            body['contiguous'] = f"*Ladder may be incomplete, starting from rank {contiguous}. Have you uploaded all the screen shots?*\n"
        else:
            body['contiguous'] = 'Yes'
            
        report = IrusReport.from_invasion(ladder)
        body['url'] = report.msg

    except Exception as e:
        status = 500
        body['url'] = f'Error generating report for {name}: {e}'

    if status == 200:
        logger.info(body)
    elif status == 401:
        logger.warning(body)
    else:
        logger.error(body)

    return {
        "statusCode": status,
        "headers": headers,
        "body": body
    }


# @logger.inject_lambda_context(log_event=True)
# def lambda_handler(event:dict, context:LambdaContext):

#     status = 200
#     headers = {
#         "Content-Type": "application/json"
#     }
#     msg = ''

#     name = event["invasion"]

#     try:
#         msg = f"#Report for Invasion {name}\n"
#         invasion = IrusInvasion.from_table(name)
#         ladder = IrusLadder.from_invasion(invasion)
#         msg += f"Ranks: {ladder.count()}\n"
#         msg += f"Members: {ladder.members()}\n"
#         contiguous = ladder.contiguous_from_1_until()
#         if contiguous != ladder.count():
#             msg += f"*Ladder may be incomplete, starting at rank {contiguous}. Are you uploaded all the screen shots?*\n"
            
#         report = IrusReport.from_invasion(ladder)
#         msg += report.msg

#     except Exception as e:
#         status = 500
#         msg = f'Error generating report for {name}: {e}'

#     if status == 200:
#         logger.info(msg)
#     elif status == 401:
#         logger.warning(msg)
#     else:
#         logger.error(msg)

#     return {
#         "statusCode": status,
#         "headers": headers,
#         "body": json.dumps(msg)
#     }