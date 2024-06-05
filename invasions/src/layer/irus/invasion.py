from boto3.dynamodb.conditions import Key
from dataclasses import dataclass
from .env import table

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

    @classmethod
    def from_user(cls, day:int, month:int, year:int, settlement:str, win:bool, notes:str = None):
        print(f'Invasion constructor: {day}, {month}, {year}, {settlement}, {win}, {notes}')

        zero_month = '{0:02d}'.format(month)
        zero_day = '{0:02d}'.format(day)
        date = f'{year}{zero_month}{zero_day}'
        name = date + '-' + settlement

        print(f'Add #invasion object for {name}')
        item = {
            'invasion': f'#invasion',
            'id': name,
            'settlememt': settlement,
            'win': win,
            'date': int(date),
            'year': year,
            'month': month,
            'day': day
        }
        if notes:
            item['notes'] = notes
        table.put_item(Item=item)

        return cls(name = name, settlement = settlement, win = win, date = date, year = year, month = month, day = day, notes = notes)

    @classmethod
    def from_table(cls, name:str):
        response = table.get_item(Key={'invasion': '#invasion', 'id': name})
        if 'Items' in response:
            item = response['Items']
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
    
