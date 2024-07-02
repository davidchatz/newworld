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


class IrusProcess:

    def __init__(self) -> None:
        self.step_func_arn = IrusResources.step_function_arn()
        self.webhook_url = IrusResources.webhook_url()


    def start(self, id: str, token: str, invasion: IrusInvasion, files: IrusFiles, process: str) -> str:

        logger.info(f'Process.start: invasion: {invasion.name} files: {files.str()} process: {process}')

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
                stateMachineArn=self.step_func_arn,
                input=json.dumps(cmd)
            )

        except ClientError as e:
            logger.warning(f'Failed to call downloader step function: {e}')
            return f'Failed to call downloader step function: {e}'

        return f'In Progress: Downloading and processing screenshot(s)'
