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
            'ladder': self.ladder
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
            'ladder': self.ladder
        }

    @classmethod
    def from_invasion_for_member(cls, invasion: IrusInvasion, member: IrusMember):
        logger.info(f'LadderRank.from_invasion_for_member: {invasion} {member}')
        ladders = table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion.name}'),
                                ProjectionExpression='id, #n, #r',
                                FilterExpression=Attr('player').eq(member.player),
                                ExpressionAttributeNames={'#n': 'name', '#r': 'rank'})
        
        if ladders.get('Items', None):
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
        return f'{self.rank} {self.player} {self.score} {self.kills} {self.deaths} {self.assists} {self.heals} {self.damage} {self.member} {self.ladder}'
 

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
        update = table.put_item(Item=self.__dict__)