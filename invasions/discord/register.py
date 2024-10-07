import urllib3
import json
import yaml
import subprocess
import shlex
import pprint
import argparse

DEFAULT_PROFILE='irus-202410'
DEFAULT_PREFIX='irustest'
#DEFAULT_PREFIX='chatzinvasionstats'

def dump_response(resp, verbose:bool):
    print(f'Status: {resp.status}')
    if verbose:
        pprint.pprint(json.loads(resp.data.decode("utf-8")))
    print('')

def list_options(command, indent='  '):
    if command["options"]:
        for c in command["options"]:
            print(f'{indent}{c["name"]}: {c["description"]}')
            if 'options' in c:
                list_options(c, indent + '  ')
            if 'choices' in c:
                for choice in c['choices']:
                    print(f'{indent}  {choice["name"]}: {choice["value"]}')


def get_param(prefix:str, param:str, profile:str) -> str:
    return subprocess.run(shlex.split(f'aws ssm get-parameter --with-decryption --name /{prefix}/{param} --profile {profile} --query Parameter.Value --output text'), stdout=subprocess.PIPE).stdout.decode('utf-8').strip()


def main():
    parser = argparse.ArgumentParser(description = "Discord slash command manager")
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument('--list', action='store_true', help='List registered commands')
    command.add_argument('--register', action='store_true', help='Register commands in commands.yaml')
    command.add_argument('--unregister', type=int, help='Unregister command ID')
    command.add_argument('--delete', action='store_true', help='Unregister all commands')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--profile', type=str, default=DEFAULT_PROFILE, help='AWS Profile')
    parser.add_argument('--prefix', type=str, default=DEFAULT_PREFIX, help='Parameter prefix')
    args = parser.parse_args()

    verbose = args.verbose
    profile = args.profile
    prefix = args.prefix

    APP_ID = get_param(prefix, 'appid', profile)
    SERVER_ID = get_param(prefix, 'serverid', profile)
    BOT_TOKEN = get_param(prefix, 'bottoken', profile)

    url = f'https://discord.com/api/v10/applications/{APP_ID}/guilds/{SERVER_ID}/commands'
    headers = {'Authorization': f'Bot {BOT_TOKEN}', 'Content-Type': 'application/json'}

    if args.list:
        print('List of commands:')
        response = urllib3.request(method='GET', url=url, headers=headers)

        if verbose:
            dump_response(response, verbose)
        else:
            commands = json.loads(response.data.decode("utf-8"))
            for c in commands:
                print(f'{c["name"]} ({c["id"]}): {c["description"]}')
                list_options(c)


    elif args.register:
        print('Registering commands:')

        with open("commands.yaml", "r") as file:
            yaml_content = file.read()

        commands = yaml.safe_load(yaml_content)

        for command in commands:
            print(f'{command["name"]}:')
            response = urllib3.request(method='POST', url=url, body=json.dumps(command), headers=headers)
            if response.status > 204:
                print(f'Error registering command: {command["name"]}')
                dump_response(response, True)
            else:
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