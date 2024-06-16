from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
from .invasion import IrusInvasion
from .environ import IrusResources

logger = IrusResources.logger()
table = IrusResources.table()

class IrusInvasionList:

    def __init__(self, items:list, start:int):
        self.invasions = []
        self.start = Decimal(start)
        for i in items:
            self.invasions.append(IrusInvasion.from_table_item(i))

    @classmethod
    def from_month(cls, month:int, year:int):
        logger.info(f'InvasionList.from_month {month}/{year}')
        zero_month = '{0:02d}'.format(month)
        date = f'{year}{zero_month}'
        start = f'{year}{zero_month}01'

        response = table.query(KeyConditionExpression=Key('invasion').eq('#invasion') & Key('id').begins_with(date))
        logger.debug(response)

        return cls(response['Items'] if 'Items' in response else [], start)


    @classmethod
    def from_start(cls, start:int):
        logger.info(f'InvasionList.from_start {start}')
        # zero_month = '{0:02d}'.format(month)
        # zero_day = '{0:02d}'.format(day)
        # start = int(f'{year}{zero_month}{zero_day}')

        response = table.query(KeyConditionExpression=Key('invasion').eq('#invasion'),
                               FilterExpression=Attr('date').gte(start))
        logger.debug(response)

        return cls(response['Items'] if 'Items' in response else [], start)


    def __str__(self) -> str:
        msg = ''
        if len(self.invasions) > 0:
            msg += self.invasions[0].name
            for i in self.invasions[1:]:
                msg += f',{i.name}'
            msg += '\n'
        
        return msg
    

    def markdown(self) -> str:
        msg = f'# Invasions from {self.start}\n'
        if len(self.invasions) == 0:
            msg += '*No invasions found*\n'
        else:
            for i in self.invasions:
                msg += f'- {i.name}\n'

        return msg


    def count(self) -> int:
        return len(self.invasions)
    
    def get(self, index:int) -> IrusInvasion:
        return self.invasions[index]