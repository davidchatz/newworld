from boto3.dynamodb.conditions import Key
from dataclasses import dataclass
from datetime import datetime
from .environ import table, logger


class Member:

    def __init__(self, item: dict):
        self.start = int(item['start'])
        self.player = item['id']
        self.faction = item['faction']
        self.admin = bool(item['admin'])
        self.salary = bool(item['salary'])
        self.discord = item['discord'] if 'discord' in item else None
        self.notes = item['notes'] if 'notes' in item else None


    @classmethod
    def from_user(cls, player:str, day:int, month:int, year:int, faction:str, discord:str, admin:bool, salary:bool, notes:str):
        logger.info(f'Member.from_user {player}')

        zero_month = '{0:02d}'.format(month)
        zero_day = '{0:02d}'.format(day)
        start = f'{year}{zero_month}{zero_day}'

        timestamp = datetime.today().strftime('%Y%m%d%H%M%S')

        additem = {
            'invasion': '#memberevent',
            'id': timestamp,
            'event': "add",
            'player': player,
            'faction': faction,
            'admin': admin,
            'salary': salary,
            'start': start
        }

        if discord:
            additem['discord'] = discord
        if notes:
            additem['notes'] = notes

        memberitem = {
            'invasion': '#member',
            'id': player,
            'faction': faction,
            'admin': admin,
            'salary': salary,
            'event': timestamp,
            'start': start
        }

        if discord:
            memberitem['discord'] = discord
        if notes:
            memberitem['notes'] = notes

        # Add event for adding this member and update list of members
        table.put_item(Item=additem)
        logger.debug(f'Put {additem}')
        table.put_item(Item=memberitem)
        logger.debug(f'Put {memberitem}')

        return cls(memberitem)


    @classmethod
    def from_table(cls, player:str):
        logger.info(f'Member.from_table {player}')

        member = table.get_item(Key={'invasion': '#member', 'id': player})

        if 'Item' not in member:
            logger.info(f'Member {player} not found in table')
            raise ValueError(f'Member {player} not found in table')

        return cls(member['Item'])


    def __str__(self):
        return f'## Member {self.player}\nFaction: {self.faction}\nStarting {self.start}\nAdmin {self.admin}\n'
    

    def remove(self) -> str:
        logger.info(f'Member.remove {self.player}')

        if not self.player:
            msg = f'Member not initialised or has been removed'
            logger.warning(f'Member not initialised or has been removed')
            raise ValueError(msg)
        
        timestamp = datetime.today().strftime('%Y%m%d%H%M%S')

        item = {
            'invasion': f'#memberevent',
            'id': timestamp,
            'event': "delete",
            'player': self.player
        }

        response = table.delete_item(Key={'invasion': f'#member', 'id': self.player}, ReturnValues='ALL_OLD')
        if 'Attributes' in response:
            mesg = f'# Removed member {self.player}'
            table.put_item(Item=item)
            self.player = None
        else:
            mesg = f'Member {self.player} not found, nothing to remove'

        logger.info(mesg)
        return mesg

