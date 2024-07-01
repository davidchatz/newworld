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
    msg = ''

    month = event["month"]

    try:
        report = IrusMonth.from_invasion_stats(month=int(month[4:6]), year=int(month[:4]))
        msg = f'# Monthly report for {month}'
        msg += f'- Invasions: {report.invasions}\n'
        msg += f'- Active Members (1 or more invasions): {len(report.report)}\n'
        msg += f'- Participation (sum of members across invasions won): {report.participation}\n'

        export = IrusReport.from_month(report)
        msg += export.msg

    except Exception as e:
        status = 500
        msg = f'Error generating report for {month}: {e}'

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
