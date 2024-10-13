from boto3.dynamodb.conditions import Key, Attr
from dataclasses import dataclass
from decimal import Decimal
from .invasion import IrusInvasion
from .member import IrusMember
from .environ import IrusResources

logger = IrusResources.logger()
table = IrusResources.table()

class IrusLadderRank:

    def __init__(self, invasion: IrusInvasion, item: dict):
        logger.debug(f'LadderRank.__init__: {invasion} {item}')
        self.invasion = invasion
        self.rank = item['rank']
        self.member = bool(item['member'])
        self.player = item['player']
        self.score = int(item['score'])
        self.kills = int(item['kills'])
        self.deaths = int(item['deaths'])
        self.assists = int(item['assists'])
        self.heals = int(item['heals'])
        self.damage = int(item['damage'])
        self.ladder = bool(item['ladder'])
        self.adjusted = bool(item['adjusted'])
        self.error = bool(item['error'])

   
    def invasion_key(self) -> str:
        return f'#ladder#{self.invasion.name}'


    def item(self) -> dict:
        return {
            'invasion': self.invasion_key(),
            'id': self.rank,
            'member': self.member,
            'player': self.player,
            'score': self.score,
            'kills': self.kills,
            'deaths': self.deaths,
            'assists': self.assists,
            'heals': self.heals,
            'damage': self.damage,
            'ladder': self.ladder,
            'adjusted': self.adjusted,
            'error': self.error
        }

    def __dict__(self) -> dict:
        return {
            'invasion': self.invasion_key(),
            'id': self.rank,
            'member': self.member,
            'player': self.player,
            'score': self.score,
            'kills': self.kills,
            'deaths': self.deaths,
            'assists': self.assists,
            'heals': self.heals,
            'damage': self.damage,
            'ladder': self.ladder,
            'adjusted': self.adjusted,
            'error': self.error
        }

    @classmethod
    def from_roster(cls, invasion:IrusInvasion, rank:int, player:str):
        return cls(invasion=invasion, item={
            'rank': '{0:02d}'.format(rank),
            'player': player,
            'score': 0,
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'heals': 0,
            'damage': 0,
            'member': True,
            'ladder': False,
            'adjusted': False,
            'error': False
        })
    
    @classmethod
    def from_invasion_for_member(cls, invasion: IrusInvasion, member: IrusMember):
        logger.info(f'LadderRank.from_invasion_for_member: {invasion} {member.str()}')
        ladders = table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion.name}'),
                                ProjectionExpression='id, #n, #r',
                                FilterExpression=Attr('player').eq(member.player),
                                ExpressionAttributeNames={'#n': 'name', '#r': 'rank'})
        
        logger.debug(f'ladders: {ladders}')
        if ladders.get('Items', None) or len(ladders['Items']) == 0:
            logger.debug(f'Player {member.player} not found in invasion {invasion.name}')
            raise ValueError(f'Player {member.player} not found in invasion {invasion.name}')
        
        items = ladders['Items']
        if len(items) > 1:
            logger.error(f'Player {member.player} matched multiple times in {invasion.name}')
            raise ValueError(f'Player {member.player} matched multiple times in {invasion.name}')
        
        # Maybe we should just store both id and rank, even though they are the same in the ladder rank
        items[0]['rank'] = items[0]['id']
        return cls(invasion, items[0])


    def __str__(self):
        return f'{self.rank} {self.player} {self.score} {self.kills} {self.deaths} {self.assists} {self.heals} {self.damage} {self.member} {self.ladder} {self.adjusted} {self.error}'
 
    def header() -> str:
        return 'Rank Player             Score Kills Deaths Assists   Heals  Damage Member Ladder Adjusted Error'

    def footer() -> str:
        return '''
*Member*: True if company member
*Ladder*: True if from ladder
*Adjusted*: True if entry corrected by bot or manually, False if unchanged from scan
*Error*: True if error detected but correct value not known
'''

    def post(self) -> str:
        return f'{self.rank:<4} {self.player:<16} {self.score:>7} {self.kills:>5} {self.deaths:>6} {self.assists:>7} {self.heals:>7} {self.damage:>7} {str(self.member):<6} {str(self.ladder):<6} {str(self.adjusted):<8} {self.error}'


    def str(self) -> str:
        return '**`' + IrusLadderRank.header()+ '`**\n`' + self.post() + '`\n' + IrusLadderRank.footer() + '\n'
    
    
    def update_membership(self, member: bool):
        logger.info(f'LadderRank.update_membership: {self} to {member}')
        self.member = member
        update = table.update_item(Key={'invasion': self.invasion_key(), 'id': self.rank},
                                    UpdateExpression='set #m = :m',
                                    ExpressionAttributeNames={'#m': 'member'},
                                    ExpressionAttributeValues={':m': member},
                                    ReturnValues='UPDATED_NEW')
        logger.debug(f'update_item: {update}')


    # method to put ladder rank into table
    def update_item(self):
        logger.debug(f'LadderRank.update_item: {self}')
        update = table.put_item(Item=self.__dict__())

    def delete_item(self):
        logger.debug(f'LadderRank.delete_item: {self}')
        delete = table.delete_item(Key={'invasion': self.invasion_key(), 'id': self.rank})
        logger.debug(f'delete_item: {delete}')