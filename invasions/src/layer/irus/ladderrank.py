from boto3.dynamodb.conditions import Key, Attr
from dataclasses import dataclass
from .env import table, logger
from .invasion import Invasion
from .member import Member

@dataclass(kw_only=True)
class LadderRank:

    invasion: Invasion
    rank: int
    member: bool
    player: str
    score: int
    kills: int
    deaths: int
    assists: int
    heals: int
    damage: int
    member: bool
    ladder: bool

    def __init__(self, invasion: Invasion, item: dict):
        logger.info(f'LadderRank.__init__: {invasion} {item}')
        self.invasion = invasion
        self.rank = item['id']
        self.member = bool(item['member'])
        self.player = item['player']
        self.score = item['score']
        self.kills = item['kills']
        self.deaths = item['deaths']
        self.assists = item['assists']
        self.heals = item['heals']
        self.damage = item['damage']
        self.ladder = bool(item['ladder'])

   
    def invasion_key(self) -> str:
        return f'#ladder#{self.invasion.name}'


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
    def from_invasion_for_member(cls, invasion: Invasion, member: Member):
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