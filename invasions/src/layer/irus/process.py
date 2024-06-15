import os
import json
from botocore.exceptions import ClientError
from .invasion import IrusInvasion
from .environ import IrusResources

resources = IrusResources()
logger = resources.logger
table = resources.table
state_machine = resources.state_machine

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


class IrusProcess:

    step_func_arn : str = None
    webhook_url : str = None

    def __init__(self):
        self.step_function_arn = os.environ.get('PROCESS_STEP_FUNC')
        self.webhook_url = os.environ.get('WEBHOOK_URL')
        if not self.step_function_arn or not self.webhook_url:
            logger.warning(f'Environment not defined {self.step_function_arn} {self.webhook_url}')
            raise ValueError(f'Environment not defined {self.step_function_arn} {self.webhook_url}')


    def start(self, id: str, token: str, invasion: IrusInvasion, files: IrusFiles, process: str) -> str:

        logger.info(f'Process.start:\nid: {id}\ntoken: {token}\ninvasion: {invasion}\nfiles: {files}\nprocess: {process}')

        cmd = {
            'post': f'{self.webhook_url}/{id}/{token}',
            'invasion': invasion.name,
            'folder': 'tbd',
            'files': files.get(),
            'process': process,
            'month': invasion.month_prefix()
        }

        if process == "Ladder":
            cmd['folder'] = invasion.path_ladders()
        elif process == "Roster":
            cmd['folder'] = invasion.path_roster()
        else:
            raise ValueError(f'invasion_screenshots: Unknown process {process}')

        logger.info(f'starting process with: {cmd}')

        try:
            state_machine.start_execution(
                stateMachineArn=self.step_function_arn,
                input=json.dumps(cmd)
            )

        except ClientError as e:
            logger.warning(f'Failed to call downloader step function: {e}')
            return f'Failed to call downloader step function: {e}'

        return f'In Progress: Downloading and processing screenshot(s)'
