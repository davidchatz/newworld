from .environ import IrusResources

resources = IrusResources()
logger = resources.logger
table = resources.table

class IrusInvasion:

    settlement_map = {
        "bw": "Brightwood",
        "bs": "Brimstone Sands",
        "ck": "Cutlass Keys",
        "er": "Ebonscale Reach",
        "eg": "Edengrove",
        "ef": "Everfall",
        "mb": "Monarchs Bluff",
        "md": "Mourningdale",
        "rw": "Reekwater",
        "rs": "Restless Shore",
        "wf": "Weavers Fen",
        "ww": "Windsward"
    }

    def __init__(self, name:str, settlement:str, win:bool, date:int, year:int, month:int, day:int, notes:str = None):
        self.name = name
        self.settlement = settlement
        self.win = bool(win)
        self.date = int(date)
        self.year = int(year)
        self.month = int(month)
        self.day = int(day)
        self.notes = notes

        if settlement not in self.settlement_map:
            raise ValueError(f'Unknown settlement {settlement}')


    def key(self):
        return {'invasion': '#invasion', 'id': self.name}
    
    @classmethod
    def from_user(cls, day:int, month:int, year:int, settlement:str, win:bool, notes:str = None):
        logger.info(f'Invasion.from_user: {day}, {month}, {year}, {settlement}, {win}, {notes}')

        if settlement not in cls.settlement_map:
            raise ValueError(f'Unknown settlement {settlement}')
        
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
            'date': int(date),
            'year': year,
            'month': month,
            'day': day
        }
        if notes:
            item['notes'] = notes
        
        logger.debug(item)
        table.put_item(Item=item)

        return cls(name = name, settlement = settlement, win = win, date = int(date), year = year, month = month, day = day, notes = notes)

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
            raise ValueError(f'No invasion found called {name}')

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

    def __str__(self) -> str:
        msg = f'{self.name}, {self.settlement}, {self.date}, {self.win}'
        if self.notes:
            msg += f', {self.notes}'
        return msg
    
    def markdown(self) -> str:
        msg = f'## Invasion {self.name}\n'
        msg += f'Settlement: {self.settlement_map[self.settlement]}\n'
        msg += f'Date: {self.date}\n'
        msg += f'Win: {self.win}\n'
        if self.notes:
            msg += f'Notes: {self.notes}\n'
        return msg

    def delete_from_table(self):
        logger.info(f'Delete {self.name} from table')
        table.delete_item(Key=self.key())


    def month_prefix(self):
        zero_month = '{0:02d}'.format(int(self.month))
        return f'{self.year}{zero_month}'
    
    def path_ladders(self):
        return f'ladders/{self.name}/'
    
    def path_roster(self):
        return f'roster/{self.name}/'