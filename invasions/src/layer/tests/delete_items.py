#!/usr/bin/env python

import boto3, sys

if len(sys.argv) != 3:
    print("Usage: delete_items.py <profile> <table>")
    sys.exit(1)

session = boto3.Session(profile_name=sys.argv[1])
table_name = sys.argv[2]
dynamodb = session.resource('dynamodb')
table = dynamodb.Table(table_name)

# s3 = session.resource('s3')
# bucket = s3.Bucket(sys.argv[1])
# bucket.object_versions.all().delete()
# print("All objects in " + sys.argv[1] + " deleted.")

result = table.scan()['Items']
with table.batch_writer() as batch:
    for item in result:
        print(f'{item['invasion']} {item['id']}')
        batch.delete_item(Key={'invasion': item['invasion'], 'id': item['id']})