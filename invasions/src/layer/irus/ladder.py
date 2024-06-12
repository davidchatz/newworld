from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from dataclasses import dataclass
from .ladderrank import IrusLadderRank
from .environ import IrusResources
from .invasion import IrusInvasion
from .member import IrusMember
from .memberlist import IrusMemberList

resources = IrusResources()
logger = resources.logger
table = resources.table
textract = resources.textract

#
# based on https://docs.aws.amazon.com/textract/latest/dg/examples-export-table-csv.html
#

# define function that takes s3 bucket and key and calls textract to import table
def import_table(bucket, key):
    # call textract
    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['TABLES']
    )
    return response

def extract_blocks(response: dict):
    blocks=response['Blocks']
    blocks_map = {}
    table_blocks = []
    for block in blocks:
        blocks_map[block['Id']] = block
        if block['BlockType'] == "TABLE":
            table_blocks.append(block)

    # print(f'extract_blocks table_blocks: {table_blocks}')
    # print(f'extract_blocks blocks_map: {blocks_map}')
    return table_blocks, blocks_map

def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        if "," in word['Text'] and word['Text'].replace(",", "").isnumeric():
                            text += '"' + word['Text'] + '"' + ' '
                        else:
                            text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] =='SELECTED':
                            text +=  'X '
    return text

def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    for relationship in table_result['Relationships']:
        if relationship['Type'] == 'CHILD':
            for child_id in relationship['Ids']:
                cell = blocks_map[child_id]
                if cell['BlockType'] == 'CELL':
                    row_index = cell['RowIndex']
                    col_index = cell['ColumnIndex']
                    if row_index not in rows:
                        # create new row
                        rows[row_index] = {}
                        
                    # get the text value
                    rows[row_index][col_index] = get_text(cell, blocks_map)
    logger.debug(f'get_rows_columns_map rows: {rows}')
    return rows


def generate_ladder_ranks(rows:list, members:IrusMemberList) -> list:
    rec = []

    for row_index, cols in rows.items():
        col_indices = len(cols.items())
        
        try:
            i = int("".join(filter(str.isnumeric, cols[1])))
            # sometimes textextract treats icon as a column
            if col_indices == 9 or col_indices == 10:
                # Name may flow into score, so be more aggresive filtering this value
                f = filter(str.isnumeric,cols[4])
                player = cols[3].rstrip()
                result = IrusLadderRank({
                    'rank': '{0:02d}'.format(i),
                    'player': player,
                    'score': int("".join(f)),
                    'kills': int(cols[5].replace(',','')),
                    'deaths': int(cols[6].replace(',','')),
                    'assists': int(cols[7].replace(',','')),
                    'heals': int(cols[8].replace(',','')),
                    'damage': int(cols[9].replace(',','')),
                    # Are they listed as a company member, this is updated in insert_db
                    'member': members.is_member(player),
                    # Are these stats from a ladder screenshot import
                    'ladder': True
                })
                rec.append(result)
            elif col_indices == 8:
                f = filter(str.isnumeric,cols[3])
                player = cols[2].rstrip()
                result = IrusLadderRank({
                    'rank': '{0:02d}'.format(i),
                    'player': player,
                    'score': int("".join(f)),
                    'kills': int(cols[4].replace(', ', '')),
                    'deaths': int(cols[5].replace(', ', '')),
                    'assists': int(cols[6].replace(', ', '')),
                    'heals': int(cols[7].replace(', ', '')),
                    'damage': int(cols[8].replace(',','')),
                    'member': members.is_member(player),
                    'ladder': True
                })
                rec.append(result)
            else:
                logger.info(f'Skipping {row_index} with {col_indices} items: {cols}')

        except Exception as e:
            logger.info(f'Skipping row {row_index}, unable to scan: {e}')

    logger.debug(f'scanned table: {rec}')
    return rec


class IrusLadder:

    def __init__(self, invasion: IrusInvasion, rec:list):
        logger.info(f'Ladder.__init__: {invasion}')
        self.ranks = rec
        self.invasion = invasion

    def invasion_key(self) -> str:
        return f'#ladder#{self.invasion.name}'


    @classmethod
    def from_image(cls, invasion:IrusInvasion, members:IrusMemberList, bucket:str, key:str):
        logger.info(f'Ladder.from_image {bucket}/{key} for {invasion.name}')

        response = import_table(bucket, key)
        table_blocks, blocks_map = extract_blocks(response)

        if len(table_blocks) == 0:
            raise ValueError(f'No invasion ladder not found in {bucket}/{key}')
        elif len(table_blocks) > 1:
            raise ValueError(f'Do not recognise invasion ladder in {bucket}/{key}')

        rows = get_rows_columns_map(table_blocks[0], blocks_map)
        rec = generate_ladder_ranks(rows, members)

        try:
            table.put_item(Item={'invasion': f'#upload#{invasion.name}', 'id': key})
            with table.batch_writer() as batch:
                for item in rec:
                    batch.put_item(Item=dict(item))
        except ClientError as err:
            logger.error(f'Failed to update table: {err}')
            raise ValueError(f'Failed to update table: {err}')

        return cls(invasion, rec)

    @classmethod
    def from_invasion(cls, invasion:IrusInvasion):
        logger.info(f'Ladder.from_invasion {invasion.name}')
        rec = []
        for item in table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion.name}'))['Items']:
            rec.append(IrusLadderRank(item))

        return cls(invasion, rec)

    # Ranks start from 1 and are contiguous
    def is_contiguous_from_1(self) -> bool:
        count = 1
        for r in self.ranks:
            if r.rank != count:
                return False
            count += 1
        return True

    def count(self) -> int:
        return len(self.ranks)
    
    def members(self) -> int:
        count = 0
        for r in self.ranks:
            count += 1 if r['member'] == True else 0
        return count
    
    def __str__(self) -> str:
        return f'Ladder for invasion {self.invasion.name} of {self.count()} ranks including {self.members()} members\n'

    def csv(self) -> str:
        msg = f'ladder for invasion {self.invasion.name}\n'
        msg += 'rank,player,score,kills,deaths,assists,heals,damage\n'
        for r in self.ranks:
            msg += f'{r.rank},{r.player},{r.score},{r.kills},{r.deaths},{r.assists},{r.heals},{r.damage}\n'
        return msg

    def markdown(self) -> str:
        msg = '# Ladder\n'
        msg += f'Ranks: {self.count()}\n'
        msg += self.invasion.markdown()
        return msg