import boto3
from botocore.exceptions import ClientError
import os
import urllib

textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

# based on https://docs.aws.amazon.com/textract/latest/dg/examples-export-table-csv.html

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
    # scores = []
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

    print(f'get_rows_columns_map rows: {rows}')
    return rows

def generate_table_csv(table_result, blocks_map, table_index):
    rows = get_rows_columns_map(table_result, blocks_map)

    table_id = 'Table_' + str(table_index)
    
    # get cells.
    csv = 'Table: {0}\n\n'.format(table_id)

    for row_index, cols in rows.items():
        for col_index, text in cols.items():
            col_indices = len(cols.items())
            csv += '{}'.format(text) + ","
        csv += '\n'
    
    return csv

def generate_table(table_result, blocks_map):
    rows = get_rows_columns_map(table_result, blocks_map)
    rec = []

    for row_index, cols in rows.items():
        col_indices = len(cols.items())
        
        try:

            i = int("".join(filter(str.isnumeric, cols[1])))
            # sometimes textextract treats icon as a column
            if col_indices == 9 or col_indices == 10:
                # Name may flow into score, so be more aggresive filtering this value
                f = filter(str.isnumeric,cols[4])
                result = {
                    'id': '{0:02d}'.format(i),
                    'name': cols[3].rstrip(),
                    'score': int("".join(f)),
                    'kills': int(cols[5].replace(',','')),
                    'deaths': int(cols[6].replace(',','')),
                    'assists': int(cols[7].replace(',','')),
                    'heals': int(cols[8].replace(',','')),
                    'damage': int(cols[9].replace(',','')),
                    # Are they listed as a company member, this is updated in insert_db
                    'member': False,
                    # Are these stats from a ladder screenshot import
                    'ladder': True
                }
                rec.append(result)
            elif col_indices == 8:
                f = filter(str.isnumeric,cols[3])
                result = {
                    'id': '{0:02d}'.format(i),
                    'name': cols[2].rstrip(),
                    'score': int("".join(f)),
                    'kills': int(cols[4].replace(', ', '')),
                    'deaths': int(cols[5].replace(', ', '')),
                    'assists': int(cols[6].replace(', ', '')),
                    'heals': int(cols[7].replace(', ', '')),
                    'damage': int(cols[8].replace(',','')),
                    'member': False,
                    'ladder': True
                }
                rec.append(result)
            else:
                print(f'Skipping {row_index} with {col_indices} items: {cols}')

        except Exception as e:
            print(f'Skipping row {row_index}, unable to scan')
            print(e)

    print(f'generate_table rec: {rec}')
    return rec

def match_member(name:str):

    member = False
    alt = name

    member = table.get_item(Key={'invasion': '#member', 'id': name})
    if 'Item' in member:
        member = True
    # If the name has a capital 'O' try searching for the name with the number '0'
    else:
        alt = name.replace('O','0')
        if alt != name:
            member = table.get_item(Key={'invasion': '#member', 'id': alt})
            if 'Item' in member:
                print(f'Matched {name} to member (alt 1) {alt}')
                member = True
            # Lastly try replace '0' with 'O'
            else:
                alt = name.replace('0','O')
                if alt != name:
                    member = table.get_item(Key={'invasion': '#member', 'id': alt})
                    if 'Item' in member:
                        print(f'Matched {name} member (alt 2) {alt}')
                        member = True

    return member, alt


def insert_db(table, invasion, result, key):

    try:
        # Add row to identity this upload
        table.put_item(Item={'invasion': f'#upload#{invasion}', 'id': key})

        for item in result:
            item['invasion'] = f'#ladder#{invasion}'

            # Check if current member and flag if they are
            member, alt = match_member(item["name"])
            if member:
                print(f'Matched member {alt} to position {item["id"]}')
                item['member'] = True
                item['name'] = alt
            else:
                item['member'] = False

        # Add ladder results from scan
        with table.batch_writer() as batch:
            for item in result:
                batch.put_item(Item=item)

    except ClientError as err:
        print(err.response['Error']['Message'])
        raise

# define lambda handler that gets S3 bucket and key from event and calls import_table
def lambda_handler(event, context):
    # get bucket and key from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    # key = event['Records'][0]['s3']['object']['key']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    folders = key.split('/')

    if len(folders) != 3:
        print(f'Skipping {key} as it is not in the correct format, expecting ladders/(invasion)/(filename).')
        raise Exception(f'Skipping {key} as it is not in the correct format')
    if folders[0] != 'ladders':
        print(f'Skipping {key} as it is not in the correct format, expecting ladders/(invasion)/(filename).')
        raise Exception(f'Skipping {key} as it is not in the correct format')
    if key[-4:] != '.png':
        print(f'Skippng {key} as it is not a PNG file')
        raise Exception(f'Skipping {key} as it is not a PNG file')

    invasion = folders[1]
    print(f'{bucket}/{key} (invasion: {invasion})')

    table = dynamodb.Table(table_name)

    # call import_table
    response = import_table(bucket, key)
    table_blocks, blocks_map = extract_blocks(response)

    if len(table_blocks) == 0:
        print(f'No table found in {bucket}/{key}')
        raise Exception(f'No table found in {bucket}/{key}')
    elif len(table_blocks) > 1:
        print(f'No table found in {bucket}/{key}')
        raise Exception(f'No table found in {bucket}/{key}')

    result = generate_table(table_blocks[0], blocks_map)
    insert_db(table, invasion, result, key)

    return f"Ladder scanned and stats updated for invasion {invasion}"
