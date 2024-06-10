import os
import json
import boto3
from botocore.exceptions import ClientError
from .environ import logger
from .invasion import Invasion

state_machine = boto3.client('stepfunctions')


class Files:

    def __init__(self, options:list, resolved:dict):
        self.files : list = []

        for o in options:
            if o["name"].startswith("file"):
                self.files.append({
                    "name": o["name"],
                    "attachment": o["value"]
                })

        for a in self.files:
            a['filename'] = resolved['attachments'][a['attachment']]['filename']
            a['url'] = resolved['attachments'][a['attachment']]['url']
        
        logger.debug(f'Files: {self.files}')

    def get(self) -> list:
        return self.files


class Process:

    step_func_arn : str = None
    webhook_url : str = None

    def __init__(self):
        self.step_function_arn = os.environ.get('PROCESS_STEP_FUNC')
        self.webhook_url = os.environ.get('WEBHOOK_URL')


    def start(self, id: str, token: str, invasion: Invasion, files: Files, process: str) -> str:

        logger.info(f'Process.start:\nid: {id}\ntoken: {token}\ninvasion: {invasion}\nfiles: {files}\nprocess: {process}')

        cmd = {
            'post': f'{self.webhook_url}/{id}/{token}',
            'invasion': invasion.name,
            'folder': 'tbd',
            'files': files.get(),
            'process': process,
            'month': invasion.month_prefix()
        }

        if process == "Ladder" or process == "Download":
            cmd['folder'] = 'ladders/' + cmd['invasion'] + '/'
        elif process == "Roster":
            cmd['folder'] = 'boards/' + cmd['invasion'] + '/'
        else:
            raise ValueError(f'invasion_screenshots: Unknown process {process}')

        logger.debug(f'cmd: {cmd}')

        try:
            state_machine.start_execution(
                stateMachineArn=self.step_function_arn,
                input=json.dumps(cmd)
            )

        except ClientError as e:
            logger.warning(f'Failed to call downloader step function: {e}')
            return f'Failed to call downloader step function: {e}'

        return f'In Progress: Downloading and processing screenshot(s)'
