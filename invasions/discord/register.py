import urllib3
import json
import yaml
import subprocess
import shlex
import pprint
import argparse

AWS_PROFILE='newworld'

def dump_response(resp, verbose:bool):
    print(f'Status: {resp.status}')
    if verbose:
        pprint.pprint(json.loads(resp.data.decode("utf-8")))
    print('')

def get_param(param) -> str:
    return subprocess.run(shlex.split(f'aws ssm get-parameter --with-decryption --name /chatzinvasionstats/{param} --profile {AWS_PROFILE} --query Parameter.Value --output text'), stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

APP_ID = get_param('appid')
SERVER_ID = get_param('chatzdev/serverid')
BOT_TOKEN = get_param('bottoken')

url = f'https://discord.com/api/v10/applications/{APP_ID}/guilds/{SERVER_ID}/commands'
headers = {'Authorization': f'Bot {BOT_TOKEN}', 'Content-Type': 'application/json'}

def main():
    parser = argparse.ArgumentParser(description = "Discord slash command manager")
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument('--list', action='store_true', help='List registered commands')
    command.add_argument('--register', action='store_true', help='Register commands in commands.yaml')
    command.add_argument('--unregister', type=int, help='Unregister command ID')
    command.add_argument('--delete', action='store_true', help='Unregister all commands')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()

    verbose = args.verbose

    if args.list:
        print('List of commands:')
        response = urllib3.request(method='GET', url=url, headers=headers)

        if verbose:
            dump_response(response, verbose)
        else:
            commands = json.loads(response.data.decode("utf-8"))
            for c in commands:
                print(f'{c["name"]} ({c["id"]}): {c["description"]}')

    elif args.register:
        print('Registering commands:')

        with open("commands.yaml", "r") as file:
            yaml_content = file.read()

        commands = yaml.safe_load(yaml_content)

        for command in commands:
            print(f'{command["name"]}:')
            response = urllib3.request(method='POST', url=url, body=json.dumps(command), headers=headers)
            dump_response(response, verbose)

    elif args.unregister:
        print(f'Unregistering command {args.unregister}:')
        response = urllib3.request(method='DELETE', url=f'{url}/{args.unregister}', headers=headers)
        dump_response(response, verbose)

    elif args.delete:
        response = urllib3.request(method='GET', url=url, headers=headers)
        commands = json.loads(response.data.decode("utf-8"))
        for command in commands:
            print(f'Unregistering command {command["id"]}:')
            response = urllib3.request(method='DELETE', url=f'{url}/{command["id"]}', headers=headers)
            dump_response(response, verbose)

    else:
        print('No arguments provided')
        exit(1)
        
if __name__ == "__main__":
    # calling the main function
    main()