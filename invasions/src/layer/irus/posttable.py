import os
import json
from botocore.exceptions import ClientError
from .invasion import IrusInvasion
from .environ import IrusResources

logger = IrusResources.logger()
table = IrusResources.table()
state_machine = IrusResources.state_machine()


class IrusFiles:

    def __init__(self):
        self.files : list = []

    def append(self, name:str, attachment:str):
        logger.debug(f'Files.append: {name} {attachment}')
        self.files.append({
            "name": name,
            "attachment": attachment
        })

    def update(self, attachments:dict):
        logger.debug(f'Attachments: {attachments}')
        for a in self.files:
            a['filename'] = attachments[a['attachment']]['filename']
            a['url'] = attachments[a['attachment']]['url']
        logger.debug(f'Files: {self.files}')
        for a in self.files:
            if 'filename' not in a:
                logger.warning(f'Missing filename for {a.name}')
                raise ValueError(f'Missing filename for {a.name}')


    def get(self) -> list:
        return self.files
    
    def str(self) -> str:
        return f'{len(self.files)} files'


class IrusPostTable:

    def __init__(self) -> None:
        self.step_func_arn = IrusResources.post_step_function_arn()
        self.webhook_url = IrusResources.webhook_url()


    def start(self, id: str, token: str, table:list, title:str) -> str:

        logger.info(f'PostTable.start: table {title} with {len(table)} rows')

        cmd = {
            'post': f'{self.webhook_url}/{id}/{token}',
            'table': table
        }

        logger.info(f'starting post table step function for {title}')

        try:
            state_machine.start_execution(
                stateMachineArn=self.step_func_arn,
                input=json.dumps(cmd)
            )

        except ClientError as e:
            logger.warning(f'Failed to call post table step function: {e}')
            return f'Failed to call post table step function: {e}'

        return title
