import urllib3
import json
import yaml
import subprocess
import shlex

AWS_PROFILE='newworld'

def dump_response(resp):
    print(f'Status: {resp.status}')
    print(resp.data.decode("utf-8"))

def get_param(param) -> str:
    return subprocess.run(shlex.split(f'aws ssm get-parameter --with-decryption --name /chatzinvasionstats/{param} --profile {AWS_PROFILE} --query Parameter.Value --output text'), stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

APP_ID = get_param('appid')
SERVER_ID = get_param('chatzdev/serverid')
BOT_TOKEN = get_param('bottoken')

# global commands are cached and only update every hour
# url = f'https://discord.com/api/v10/applications/{APP_ID}/commands'

# while server commands update instantly
# they're much better for testing
url = f'https://discord.com/api/v10/applications/{APP_ID}/guilds/{SERVER_ID}/commands'
print(f'url: {url}')

with open("commands.yaml", "r") as file:
    yaml_content = file.read()

commands = yaml.safe_load(yaml_content)

headers = {'Authorization': f'Bot {BOT_TOKEN}', 'Content-Type': 'application/json'}

for command in commands:
    print(f'{command["name"]}:')
    response = urllib3.request(method='POST', url=url, body=json.dumps(command), headers=headers)
    dump_response(response)