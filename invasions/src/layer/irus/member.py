from boto3.dynamodb.conditions import Key
from dataclasses import dataclass
from datetime import datetime
from .env import table

@dataclass
class Member:

    start: int
    player: str
    faction: str
    admin: bool
    discord: str
    notes: str

    @classmethod
    def from_user(cls, player:str, day:int, month:int, year:int, faction:str, discord:str, admin:bool, notes:str):

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
            'event': timestamp,
            'start': start
        }

        if discord:
            memberitem['discord'] = discord
        if notes:
            memberitem['notes'] = notes

        # Add event for adding this member and update list of members
        table.put_item(Item=additem)
        table.put_item(Item=memberitem)

        return cls(player = player, faction = faction, admin = admin, start = start, discord = discord, notes = notes)


    def __str__(self):
        return f'## New member {player}\nFaction: {faction}\nStarting {start}\nAdmin {admin}\n'

