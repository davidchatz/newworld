import os
import boto3
import boto3.session
import pytest
import json
from aws_lambda_powertools import Logger
from .lambdaclient import LambdaClient
from irus import IrusInvasion, IrusMember, IrusMemberList, IrusLadder, IrusMonth


client = LambdaClient(local=True)

logger = Logger(service="test_month", level="INFO", correlation_id=True)
dynamodb = client.session.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

s3 = client.session.resource('s3')
test_bucket_name = os.environ['TEST_BUCKET_NAME']
test_bucket = s3.Bucket(test_bucket_name)
bucket_name = os.environ['BUCKET_NAME']
bucket = s3.Bucket(bucket_name)



@pytest.fixture
def generate_20240611():
    invasion_20240611 = IrusInvasion.from_user(day=11, month=6, year=2024, settlement='rw', win=True)

    Chatz01 = IrusMember.from_user(player = "Chatz01", day=1, month=5, year=2024, faction= "purple", admin=False, salary=True)
    Stuggy = IrusMember.from_user(player = "Stuggy", day=1, month=5, year=2024, faction= "green", admin=True, salary=True)
    Zel0s = IrusMember.from_user(player = "Zel0s", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    SunnieGal = IrusMember.from_user(player = "SunnieGal", day=1, month=5, year=2024, faction= "purple", admin=False, salary=False)
    Merkavar = IrusMember.from_user(player = "Merkavar", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    Fred = IrusMember.from_user(player = "Fred", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)

    SeaCoconut = IrusMember.from_user(player = "Sea Coconut", day=1, month=5, year=2024, faction= "purple", admin=False, salary=True)
    TaliMonk = IrusMember.from_user(player = "TaliMonk", day=1, month=5, year=2024, faction= "green", admin=True, salary=True)
    AbuHurayra = IrusMember.from_user(player = "Abu Hurayra", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    Steve = IrusMember.from_user(player = "Steve", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    LovingMum = IrusMember.from_user(player = "Loving Mum", day=1, month=5, year=2024, faction= "purple", admin=False, salary=True)
    kbaz = IrusMember.from_user(player = "kbaz", day=1, month=5, year=2024, faction= "green", admin=True, salary=True)
    SirCandeez = IrusMember.from_user(player = "Sir Candeez", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    Julie = IrusMember.from_user(player = "Julie", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)

    members = IrusMemberList()

    csv = '''
01,Shen Yi,157248,151,0,136,0,7416913
02,ABYZZMOS,121610,159,1,221,0,5575032
03,Stuggy,111079,102,0,170,0,5214001
04,Request IV,108017,200,1,481,0,4660642
05,KiCkJr,98876,82,1,161,0,4658310
06,nyapsak,96040,111,0,146,0,4451500
07,I-Cooper-l,95760,44,0,87,0,4634523
08,Chatz01,75163,77,0,125,0,3503171
09,Loving Mum,74324,83,1,169,0,3424212
10,FireSurge21,72329,110,0,166,5247,3255866
11,OniYun,68515,83,0,377,0,3029781
12,KinYager,66537,53,1,131,0,3128901
13,Wizdi,59197,66,0,96,0,2746869
14,Abu Hurayra,56366,70,1,127,0,2579804
15,Lizenlo,55466,76,0,175,0,2495815
16,kbaz,54056,43,1,101,0,2544810
17,MrDupati,49450,37,0,64,0,2347607
18,SheepDog,48816,78,3,184,0,2153829
19,Golem Designer,45680,44,3,128,0,2110009
20,VoidL3ss,45647,42,0,136,0,2115393
21,Tauenga,45547,24,0,73,0,2180878
22,SheKuntrinx,43092,32,4,163,0,1993108
23,uuiunW,41163,54,0,108,0,1872524
24,Lilaska,40949,28,0,103,0,1925978
25,Azzurri,40728,29,0,126,0,1900923
26,Zel0s,38244,46,1,93,0,1750720
27,SunnieGal,37202,36,0,201,0,1669639
28,Marropea,37150,60,1,140,0,1637544
29,Ser Smash,35974,3,2,39,0,1773017
30,Dave the Farmer,35538,17,1,147,0,1660919
31,Ryzennn,35264,50,2,122,0,1577237
32,Jaddsie,32478,42,0,154,0,1441914
33,G,31245,25,0,74,0,1462769
34,Sir Candeez,29142,18,2,47,0,1368859
35,GhostWilliam,26912,24,0,63,0,1254878
36,Jatix /,26695,19,0,52,0,1262341
37,T3K-DOGGO,24714,22,0,64,0,1119992
38,C4pitoshka,23757,9,2,52,0,1139358
39,sunnieboy,22771,20,3,149,533262,747463
40,Baratlek,21227,18,0,145,0,943864
41,VeEnaaa97,20123,9,2,41,0,963177
42,Cakeyy,19988,16,0,67,0,925931
43,Shirai - XXXIII -,17914,15,2,118,0,799221
44,IHazMagics,17655,12,0,73,211835,710355
45,MiLkMaN AU,16387,11,1,42,0,770869
46,BossMadam,14849,1,1,50,577400,430233
47,KingSeanTV,13935,17,0,43,0,632786
48,SomebodysFridge,13810,2,0,52,794488,262769
49,Pennelope Death,12204,5,0,48,483729,329887
50,Merkavar,11569,20,0,20,0,429938
51,SuperJetski,5758,4,0,4,0,275905
52,Dinyeros,0,0,0,0,0,0'''

    ladders = IrusLadder.from_csv(invasion_20240611, csv, members)
    month = IrusMonth.from_invasion_stats(month = 6, year = 2024)

    event = {
        'invasion': invasion_20240611.name,
        'filename': 'one.png',
        'month': '202406',
        'url': 'https://bogus.example.com',
        'folder': invasion_20240611.path_ladders(),
        'process': 'ladder'
    }

    logger.debug(f'Event: {event}')

    result = client.lambda_client.invoke(FunctionName='Month',
                                         InvocationType='RequestResponse',
                                         Payload=json.dumps(event))
    logger.debug(f'Result: {result}')

    response = json.loads(result['Payload'].read())
    logger.info(f'Result payload: {response}')

    yield response
    month.delete_from_table()
    ladders.delete_from_table()
    invasion_20240611.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()
    Zel0s.remove()
    SunnieGal.remove()
    Merkavar.remove()
    Fred.remove()
    SeaCoconut.remove()
    AbuHurayra.remove()
    TaliMonk.remove()
    Steve.remove()
    LovingMum.remove()
    kbaz.remove()
    SirCandeez.remove()
    Julie.remove()


def test_generate_20240611(generate_20240611):
    assert generate_20240611['statusCode'] == 200
    logger.info(generate_20240611['body'])


