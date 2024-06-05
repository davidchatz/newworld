from boto3.dynamodb.conditions import Key
from dataclasses import dataclass
from .invasion import Invasion
from .env import table

class InvasionList:

    invasions: list[Invasion]
    date: int

    def __init__(self, month, year):
        zero_month = '{0:02d}'.format(month)
        self.date = f'{year}{zero_month}'

        response = table.query(KeyConditionExpression=Key('invasion').eq('#invasion') & Key('id').begins_with(self.date),
                            ProjectionExpression='id')
        print(response)
        if 'Items' in response:
            for i in response['Items']:
                invasions += Invasion.from_table_item(i)

    def __str__(self):
        msg = ''
        if len(self.invasions) == 0:
            msg = f'No invasions found for month of {self.date}'
        else:
            msg = f'# Invasion List for {self.date}\n'
            for i in self.invasions:
                msg += f'- {i.name()}\n'
        
        return msg