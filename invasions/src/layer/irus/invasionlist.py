from boto3.dynamodb.conditions import Key, Attr
from dataclasses import dataclass
from .invasion import Invasion
from .env import table, logger

class InvasionList:

    invasions: list[Invasion]
    date: int

    def __init__(self, items:list, date:int):
        for i in items:
            self.invasions += Invasion.from_table_item(i)

    @classmethod
    def from_month(cls, month:int, year:int):
        logger.info(f'InvasionList.from_month {month}/{year}')
        zero_month = '{0:02d}'.format(month)
        date = f'{year}{zero_month}'

        response = table.query(KeyConditionExpression=Key('invasion').eq('#invasion') & Key('id').begins_with(date))
        logger.debug(response)

        return cls(response['Items'] if 'Items' in response else [], date)


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


    def __str__(self):
        msg = ''
        if len(self.invasions) == 0:
            msg = f'No invasions found for month of {self.date}'
        else:
            msg = f'# Invasion List for {self.date}\n'
            for i in self.invasions:
                msg += f'- {i.name()}\n'
        
        return msg


    def count(self) -> int:
        return len(self.invasions)