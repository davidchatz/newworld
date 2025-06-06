from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from dataclasses import dataclass
from decimal import Decimal
from .ladderrank import IrusLadderRank
from .environ import IrusResources
from .invasion import IrusInvasion
from .memberlist import IrusMemberList

logger = IrusResources.logger()
table = IrusResources.table()
textract = IrusResources.textract()

#
# Ladder image processing
# based on https://docs.aws.amazon.com/textract/latest/dg/examples-export-table-csv.html
#

# define function that takes s3 bucket and key and calls textract to import table
def import_ladder_table(bucket, key):
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


def numeric(orig:str) -> int:
    return int("".join(filter(str.isnumeric, orig)))

def generate_ladder_ranks(invasion:IrusInvasion, rows:list, members:IrusMemberList) -> list:
    rec = []

    for row_index, cols in rows.items():
        col_indices = len(cols.items())
        
        try:
            # sometimes textextract treats icon as a column, so check columns detected
            offset = 0 if col_indices == 8 else 1
            if col_indices >= 8 or col_indices <= 10:
                # Name may flow into score, so be more aggresive filtering this value
                player = cols[2+offset].rstrip()
                # allow partial matches, but flag it as adjusted
                adjusted=False
                member = members.is_member(player, partial=False)
                if not member:
                    member = members.is_member(player, partial=True)
                    if member:
                        adjusted=True
                result = IrusLadderRank(invasion=invasion, item={
                    'rank': '{0:02d}'.format(numeric(cols[1])),
                    'player': member if member else player,
                    'score': numeric(cols[3+offset]),
                    'kills': numeric(cols[4+offset]),
                    'deaths': numeric(cols[5+offset]),
                    'assists': numeric(cols[6+offset]),
                    'heals': numeric(cols[7+offset]),
                    'damage': numeric(cols[8+offset]),
                    # Are they listed as a company member, this is updated in insert_db
                    'member': True if member else False,
                    # Are these stats from a ladder screenshot import
                    'ladder': True,
                    'adjusted': adjusted,
                    'error': False
                })

                # If score and damage is zero, assume they did not participate
                if result.score > 0:
                    rec.append(result)
                else:
                    logger.info(f'Skipping {result} as score is 0')
            else:
                logger.info(f'Skipping {row_index} with {col_indices} items: {cols}')

        except Exception as e:
            logger.info(f'Skipping row {row_index} with {cols}, unable to scan: {e}')

    # With larger scans textract struggles with the rank column
    # Traverse the list of ranks and try to correct any values which are clearly wrong
    # This is particularly trick if the first row is wrong...

    # If we scanned 3 or less don't try to fix as we don't have enough context
    if len(rec) > 3:

        # check ranks are in range as they sometimes get an extra number on the end
        try:
            for r in range(0, len(rec)):
                if numeric(rec[r].rank) > 99:
                    logger.info(f'Fixing rank {r+1} from {rec[r].rank} to {rec[r].rank[:2]}')
                    rec[r].rank = rec[r].rank[:2]
                    rec[r].adjusted = True
        except Exception as e:
            logger.error(f'Unable to fix rank size: {e}')

        # now check order
        try:
            for r in range(0, len(rec)-1):
                if numeric(rec[r].rank) > numeric(rec[r+1].rank):
                    logger.info(f'Fixing rank {r+1} from {rec[r].rank} to {numeric(rec[r+1].rank) - 1}')
                    rec[r].rank = '{0:02d}'.format(numeric(rec[r+1].rank) - 1)
                    rec[r].adjusted = True
        except Exception as e:
            logger.error(f'Unable to fix rank order: {e}')

        pos = numeric(rec[0].rank)
        for r in range(1, len(rec)):
            pos += 1
            if numeric(rec[r].rank) != pos:
                logger.warning(f'Rank {r} is {rec[r].rank}, expected {pos}')
                rec[r].error = True

    logger.debug(f'scanned table: {rec}')
    return rec

#
# Roster image processing
#

def import_roster_table(bucket, key):
    # call textract
    response = textract.detect_document_text(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}}
    )
    # print(response)
    return response


def reduce_list(table: dict) -> list:
    logger.debug(f'IrusLadder.reduce_list')
    response = []

    for block in table['Blocks']:
        if block['BlockType'] != 'PAGE':
            text = block['Text']

            if not (text.isnumeric() or text == ':' or text.startswith('GROUP')):
                response.append(text)

    logger.debug(f'reduce_list: {response}')
    return response


def member_match(candidates: list, members:IrusMemberList) -> list:

    matched = []
    unmatched = []

    sorted_candidates = sorted(set(candidates))
    logger.debug(f'sorted_candidates ({len(sorted_candidates)}): {sorted_candidates}')

    for c in sorted_candidates:
        player = members.is_member(c, partial = True)
        if player:
            matched.append(player)
        else:
            unmatched.append(c)

    # Sort again in case we matched multiple times to the same player, yes this can happen
    sorted_matched = sorted(set(matched))

    logger.debug(f'matched ({len(sorted_matched)}): {sorted_matched}')
    logger.debug(f'unmatched ({len(unmatched)}): {unmatched}')

    return sorted_matched


def generate_roster_ranks(invasion:IrusInvasion, matched:list) -> list:
    rec = []

    rank = 1
    for m in matched:
        result = IrusLadderRank.from_roster(invasion=invasion, rank=rank, player=m)
        rec.append(result)
        rank += 1 

    logger.debug(f'roster: {rec}')
    return rec


class IrusLadder:

    def __init__(self, invasion: IrusInvasion, rec:list):
        logger.info(f'IrusLadder.__init__: {invasion}')
        logger.debug(f'{rec}')
        self.ranks = rec
        self.invasion = invasion

    def invasion_key(self) -> str:
        return f'#ladder#{self.invasion.name}'


    @classmethod
    def from_ladder_image(cls, invasion:IrusInvasion, members:IrusMemberList, bucket:str, key:str):
        logger.info(f'Ladder.from_ladder_image {bucket}/{key} for {invasion.name}')

        response = import_ladder_table(bucket, key)
        table_blocks, blocks_map = extract_blocks(response)

        if len(table_blocks) == 0:
            raise ValueError(f'No invasion ladder not found in {bucket}/{key}')
        elif len(table_blocks) > 1:
            raise ValueError(f'Do not recognise invasion ladder in {bucket}/{key}')

        rows = get_rows_columns_map(table_blocks[0], blocks_map)
        rec = generate_ladder_ranks(invasion, rows, members)

        try:
            table.put_item(Item={'invasion': f'#upload#{invasion.name}', 'id': key})
            with table.batch_writer() as batch:
                for item in rec:
                    batch.put_item(Item=item.item())
        except ClientError as err:
            logger.error(f'Failed to update table: {err}')
            raise ValueError(f'Failed to update table: {err}')

        return cls(invasion, rec)


    @classmethod
    def from_roster_image(cls, invasion:IrusInvasion, members:IrusMemberList, bucket:str, key:str):
        logger.info(f'Ladder.from_roster_image {bucket}/{key} for {invasion.name}')

        response = import_roster_table(bucket, key)
        candidates = reduce_list(response)
        matched = member_match(candidates, members)
        rec = generate_roster_ranks(invasion, matched)

        try:
            table.put_item(Item={'invasion': f'#upload#{invasion.name}', 'id': key})
            with table.batch_writer() as batch:
                for item in rec:
                    batch.put_item(Item=item.item())
        except ClientError as err:
            logger.error(f'Failed to update table: {err}')
            raise ValueError(f'Failed to update table: {err}')

        return cls(invasion, rec)


    @classmethod
    def from_invasion(cls, invasion:IrusInvasion):
        logger.info(f'Ladder.from_invasion {invasion.name}')
        rec = []
        for item in table.query(KeyConditionExpression=Key('invasion').eq(f'#ladder#{invasion.name}'))['Items']:
            item['rank'] = item['id']
            rec.append(IrusLadderRank(invasion, item))

        return cls(invasion, rec)


    @classmethod
    def from_csv(cls, invasion:IrusInvasion, csv:str, members:IrusMemberList):
        logger.info(f'Ladder.from_csv {invasion.name}')
        rec = []
        lines = csv.splitlines()
        for line in lines[1:]:
            cols = line.split(',')
            if (len(cols) == 8):
                item = {
                    'rank': cols[0],
                    'player': cols[1],
                    'score': int(cols[2]),
                    'kills': int(cols[3]),
                    'deaths': int(cols[4]),
                    'assists': int(cols[5]),
                    'heals': int(cols[6]),
                    'damage': int(cols[7]),
                    'member': members.is_member(cols[1]),
                    'ladder': True,
                    'adjusted': False,
                    'error': False
                }
                rec.append(IrusLadderRank(invasion, item))

        try:
            table.put_item(Item={'invasion': f'#upload#{invasion.name}', 'id': 'csv'})
            with table.batch_writer() as batch:
                for item in rec:
                    batch.put_item(Item=item.item())
        except ClientError as err:
            logger.error(f'Failed to update table: {err}')
            raise ValueError(f'Failed to update table: {err}')

        return cls(invasion, rec)


    # Ranks start from 1 and are contiguous until return value
    # Compare result to count() to confirm ladder is contiguous
    def contiguous_from_1_until(self) -> int:
        count = 0
        for r in self.ranks:
            count += 1
            if int(r.rank) != count:
                logger.debug(f's_contiguous_from_1: Rank {r.rank} is not {count}')
                return count
        return count

    def count(self) -> int:
        return len(self.ranks)
    
    # only count members that scored in the invasion
    def members(self) -> int:
        count = 0
        for r in self.ranks:
            count += 1 if (r.member == True and (r.ladder == False or (r.ladder == True and r.score > 0))) else 0
        return count
    
    def rank(self, rank:int) -> IrusLadderRank:
        for r in self.ranks:
            if int(r.rank) == rank:
                return r
        return None
    
    # Return a row in the ladder for a player who was a member at the time of the invasion and scored
    def member(self, player:str) -> IrusLadderRank:
        for r in self.ranks:
            if r.player == player and r.member == True and (r.ladder == False or (r.ladder == True and r.score > 0)):
                return r
        return None

    def list(self, member: bool) -> str:
        mesg = ''
        for r in self.ranks:
            if r.member == member:
                if r.error:
                    mesg += '**'
                elif r.adjusted:
                    mesg += '*'
                mesg += f'[{r.rank}] {r.player}'
                if r.error:
                    mesg += '**'
                elif r.adjusted:
                    mesg += '*'
                mesg += ', '                
        return mesg

    def str(self) -> str:
        return f'Ladder for invasion {self.invasion.name} with {self.count()} rank(s) including {self.members()} member(s)'

    def csv(self) -> str:
        msg = f'ladder for invasion {self.invasion.name}\n'
        msg += 'rank,player,score,kills,deaths,assists,heals,damage,scan\n'
        for r in self.ranks:
            if r.error:
                scan = 'error'
            elif r.adjusted:
                scan = 'adjusted'
            else:
                scan = 'ok'
            msg += f'{r.rank},{r.player},{r.score},{r.kills},{r.deaths},{r.assists},{r.heals},{r.damage},scan\n'
        return msg

    def markdown(self) -> str:
        msg = '# Ladder\n'
        msg += f'Ranks: {self.count()}\n'
        msg += self.invasion.markdown()
        return msg

    def post(self) -> list:
        msg = self.invasion.post()
        msg.append(f'Ranks: {self.count()}')
        msg.append(IrusLadderRank.header())
        for r in self.ranks:
            msg.append(r.post())
        msg.append(IrusLadderRank.footer())
        return msg

    def delete_from_table(self):
        logger.info(f'IrusLadder.delete_from_table for {self.invasion.name}')
        try:
            with table.batch_writer() as batch:
                for r in self.ranks:
                    batch.delete_item(Key={'invasion': f'#ladder#{self.invasion.name}', 'id': r.rank})
        except ClientError as err:
            logger.error(f'Failed to delete from table: {err}')
            raise ValueError(f'Failed to delete from table: {err}')
        
    def edit(self, rank:int, new_rank, member, player, score) -> str:

        logger.info(f'IrusLadder.edit {rank} {new_rank} {member} {player} {score}')
        r = self.rank(rank)
        if r:
            if new_rank is None:
                logger.debug(f'IrusLadder.edit -> Updating rank {rank}')
                msg = f'Updating rank {rank} in invasion {self.invasion.name}: '
            elif int(new_rank) != rank:
                logger.debug(f'IrusLadder.edit -> Replacing rank {new_rank} with rank {rank}')
                msg = f'Replacing rank {new_rank} in invasion {self.invasion.name} : '
                r.delete_item()
                r.rank = '{0:02d}'.format(new_rank)

            if member is not None:
                msg += f'\nmember {r.member} -> {member}'
                r.member = bool(member)
                r.adjusted = True
            if player:
                msg += f'\nplayer {r.player} -> {player}'
                r.player = player
                r.adjusted = True
            if score:
                msg += f'\nscore {r.score} -> {score}'
                r.score = int(score)
                r.adjusted = True
            logger.debug(f'IrusLadder.edit -> Applying update {r}')
            r.update_item()
            msg += '\n' + r.str()
        elif player is None:
            msg = f'Rank {rank} in invasion {self.invasion.name} not found, need to provide player name to add new row'
        elif new_rank is not None and int(new_rank) != rank:
            msg = f'Rank {rank} does not exist to replace new rank {new_rank}'
        else:
            msg = f'Creating new entry for rank {rank} in invasion {self.invasion.name}'

            item = {
                'rank': '{0:02d}'.format(rank),
                'player': player,
                'score': 0,
                'kills': 0,
                'deaths': 0,
                'assists': 0,
                'heals': 0,
                'damage': 0,
                'member': False,
                'ladder': False,
                'adjusted': True,
                'error': False
            }

            if score:
                item['score'] = int(score)
            if member is not None:
                item['member'] = bool(member)

            r = IrusLadderRank(self.invasion, item)
            r.update_item()
            self.ranks.append(r)
            msg += '\n' + r.str()

        logger.debug(f'IrusLadder.edit -> {msg}')

        return msg