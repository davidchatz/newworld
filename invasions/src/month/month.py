import json
from irus import IrusResources, IrusReport, IrusMonth
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = IrusResources.logger()

# define lambda handler that gets S3 bucket and key from event and calls import_table
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event:dict, context:LambdaContext):

    status = 200
    headers = {
        "Content-Type": "application/json"
    }

    month = event["month"]

    body = {
        'template': '''
        # Report for Month {}
        Invasions: {}
        Active Members: {}
        Participation (sum of members across invasions): {}
        {}
        ''',
        'month': month,
        'invasions': '0',
        'members': '0',
        'participation': '0',
        'url': 'TBD'
    }

    try:
        report = IrusMonth.from_invasion_stats(month=int(month[4:6]), year=int(month[:4]))
        body['invasions'] = report.invasions
        body['members'] = len(report.report)
        body['participation'] = report.participation

        export = IrusReport.from_month(report)
        body['url'] = export.msg

    except Exception as e:
        status = 500
        body['url'] = f'Error generating report for {month}: {e}'

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
