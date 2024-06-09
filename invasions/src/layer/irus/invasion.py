import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from dataclasses import dataclass
from aws_lambda_powertools import Logger
from .environ import table, logger


@dataclass(kw_only=True)
class Invasion:

    name: str
    settlement: str
    win: bool
    date: int
    year: int
    month: int
    day: int
    notes: str

    def key(self):
        return {'invasion': '#invasion', 'id': self.name}
    
    @classmethod
    def from_user(cls, day:int, month:int, year:int, settlement:str, win:bool, notes:str = None):
        logger.info(f'Invasion.from_user: {day}, {month}, {year}, {settlement}, {win}, {notes}')

        zero_month = '{0:02d}'.format(month)
        zero_day = '{0:02d}'.format(day)
        date = f'{year}{zero_month}{zero_day}'
        name = date + '-' + settlement

        logger.info(f'Add #invasion object for {name}')
        item = {
            'invasion': f'#invasion',
            'id': name,
            'settlement': settlement,
            'win': win,
            'date': Decimal(date),
            'year': year,
            'month': month,
            'day': day
        }
        if notes:
            item['notes'] = notes
        
        logger.debug(item)
        logger.debug(table)
        table.put_item(Item=item)

        return cls(name = name, settlement = settlement, win = win, date = Decimal(date), year = year, month = month, day = day, notes = notes)

    @classmethod
    def from_table(cls, name:str):
        logger.info(f'Invasion.from_table: {name}')
        response = table.get_item(Key={'invasion': '#invasion', 'id': name})
        logger.debug(response)
        if 'Item' in response:
            item = response['Item']
            return cls(name = item['id'],
                       settlement = item['settlement'],
                       win = item['win'],
                       date = item['date'],
                       year = item['year'],
                       month = item['month'],
                       day = item['day'],
                       notes = item['notes'] if 'notes' in item else None
                    )
        else:
            raise ValueError(f'Invasion {name} not found in table')

    @classmethod
    def from_table_item(cls, item:dict):
        logger.info(f'Invasion.from_table_item: {item}')
        return cls(name = item['id'],
                    settlement = item['settlement'],
                    win = item['win'],
                    date = item['date'],
                    year = item['year'],
                    month = item['month'],
                    day = item['day'],
                    notes = item['notes'] if 'notes' in item else None
                )

    def name(self) -> str:
        return self.name

    def __str__(self) -> str:
        msg = f'## Invasion {self.name}\n'
        msg += f'Settlement: {self.settlement}\n'
        msg += f'Date: {self.date}\n'
        msg += f'Win: {self.win}\n'
        if self.notes:
            msg += f'Notes: {self.notes}\n'
        return msg
    

    def delete_from_table(self):
        logger.info(f'Delete {self.name} from table')
        table.delete_item(Key=self.key())