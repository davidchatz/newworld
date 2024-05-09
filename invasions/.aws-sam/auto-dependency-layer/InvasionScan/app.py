import boto3

# based on https://docs.aws.amazon.com/textract/latest/dg/examples-export-table-csv.html

# define function that takes s3 bucket and key and calls textract to import table
def import_table(bucket, key):
    # call textract
    textract = boto3.client('textract')
    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['TABLES']
    )
    # return response
    print(response)
    return response

def extract_blocks(response: dict):
    blocks=response['Blocks']
    blocks_map = {}
    table_blocks = []
    for block in blocks:
        blocks_map[block['Id']] = block
        if block['BlockType'] == "TABLE":
            table_blocks.append(block)

    print(table_blocks)
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
    scores = []
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
                    
                    # get confidence score
                    scores.append(str(cell['Confidence']))
                        
                    # get the text value
                    rows[row_index][col_index] = get_text(cell, blocks_map)
    return rows, scores

def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    scores = []
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
                    
                    # get confidence score
                    scores.append(str(cell['Confidence']))
                        
                    # get the text value
                    rows[row_index][col_index] = get_text(cell, blocks_map)
    return rows, scores

def generate_table_csv(table_result, blocks_map, table_index):
    rows, scores = get_rows_columns_map(table_result, blocks_map)

    table_id = 'Table_' + str(table_index)
    
    # get cells.
    csv = 'Table: {0}\n\n'.format(table_id)

    for row_index, cols in rows.items():
        for col_index, text in cols.items():
            col_indices = len(cols.items())
            csv += '{}'.format(text) + ","
        csv += '\n'
    
    return csv


# define lambda handler that gets S3 bucket and key from event and calls import_table
def lambda_handler(event, context):
    # get bucket and key from event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    print(f'{bucket}/{key}')
    # call import_table
    response = import_table(bucket, key)
    table_blocks, blocks_map = extract_blocks(response)

    if len(table_blocks) == 0:
        return "No table found"
    
    csv = ''
    for index, table in enumerate(table_blocks):
        csv += generate_table_csv(table, blocks_map, index +1)
        csv += '\n\n'

    # return response
    print(csv)
    return csv
