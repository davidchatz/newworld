import json
from botocore.exceptions import ClientError
from .environ import IrusResources

logger = IrusResources.logger()
table = IrusResources.table()
state_machine = IrusResources.state_machine()


class IrusPostTable:

    def __init__(self) -> None:
        self.step_func_arn = IrusResources.post_step_function_arn()
        self.webhook_url = IrusResources.webhook_url()


    def start(self, id: str, token: str, table:list, title:str) -> str:

        logger.info(f'PostTable.start: table {title} with {len(table)} rows')

        cmd = {
            'post': f'{self.webhook_url}/{id}/{token}',
            'msg': [],
            'count': 0
        }

        count = 1
        msg = title + '\n'
        for t in table:
            if len(msg) + len(t) > 1995:
                cmd['msg'].append(msg)
                msg = '`' + t + '`\n'
                count += 1
            else:
                msg = msg + '`' + t + '`\n'
        cmd['msg'].append(msg)

        if count > 4:
            logger.warning(f'Too many rows ({count}) to post {title}')

        cmd['count'] = count

        logger.info(f'Starting table step function for {title} with {len(cmd["msg"])} posts')

        try:
            state_machine.start_execution(
                stateMachineArn=self.step_func_arn,
                input=json.dumps(cmd)
            )

        except ClientError as e:
            logger.warning(f'Failed to call post table step function: {e}')
            return f'Failed to call post table step function: {e}'

        return title
