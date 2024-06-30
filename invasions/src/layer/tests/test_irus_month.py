import os
import boto3
import boto3.session
import pytest
from aws_lambda_powertools import Logger
from ..irus import IrusInvasion, IrusMember, IrusMemberList, IrusLadder, IrusMonth

logger = Logger(service="test_irus_invasion", level="INFO", correlation_id=True)
profile = os.environ["AWS_PROFILE"]
session = boto3.session.Session(profile_name=profile)
dynamodb = session.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)
s3 = session.resource('s3')
test_bucket_name = os.environ['TEST_BUCKET_NAME']
test_bucket = s3.Bucket(test_bucket_name)
bucket_name = os.environ['BUCKET_NAME']
bucket = s3.Bucket(bucket_name)


@pytest.fixture
def generate_report_202405():
    invasion = IrusInvasion.from_user(day=24, month=5, year=2024, settlement='bw', win=True)
    logger.debug(f'Invasion {invasion}')

    Chatz01 = IrusMember.from_user(player = "Chatz01", day=1, month=5, year=2024, faction= "purple", admin=False, salary=True)
    Stuggy = IrusMember.from_user(player = "Stuggy", day=1, month=5, year=2024, faction= "green", admin=True, salary=True)
    Zel0s = IrusMember.from_user(player = "Zel0s", day=1, month=5, year=2024, faction= "yellow", admin=False, salary=True)
    SunnieGal = IrusMember.from_user(player = "SunnieGal", day=1, month=5, year=2024, faction= "purple", admin=False, salary=False)
    GMaaa = IrusMember.from_user(player = "G Maaaa", day=1, month=5, year=2024, faction= "green", admin=True, salary=False)
    members = IrusMemberList()

    roster = IrusLadder.from_roster_image(invasion, members, bucket_name, f'{invasion.path_roster()}20240524-bw-board-groups.png')

    month = IrusMonth.from_invasion_stats(month = 5, year = 2024)
    logger.debug(f'Month: {month}')

    yield month
    month.delete_from_table()
    invasion.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()
    Zel0s.remove()
    SunnieGal.remove()
    GMaaa.remove()


@pytest.fixture
def generate_report_202406():
    invasion_20240611 = IrusInvasion.from_user(day=11, month=6, year=2024, settlement='rw', win=True)
    invasion_20240623 = IrusInvasion.from_user(day=23, month=6, year=2024, settlement='rw', win=True)

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

    csv ='''
01,nyapsak,140048,148,1,169,0,6547912
02,Stuggy,139643,139,0,182,0,6543710
03,KiCkJr,121970,97,2,154,0,5778975
04,MorrisZ,116174,105,0,124,665,5483882
05,Decimx,115052,212,6,369,0,5038077
06,Robbie420,98705,68,0,115,0,4707765
07,DrHoOn,92543,121,0,209,0,4220186
08,ABYZZMOS,91978,91,2,112,0,4319102
09,FireSurge21,90104,141,4,173,0,4066201
10,Muninn,84812,89,6,80,0,4004766
11,Loving Mum,78982,122,0,141,0,3573633
12,Shen Yi,67055,67,2,126,0,3152734
13,Abu Hurayra,65351,57,1,326,0,2962091
14,Dallasys,65307,51,1,110,0,3082885
15,KingSeanTV,61870,24,3,94,0,2986528
16,Sea Coconut,58640,79,4,64,0,2702523
17,deodeumi,54967,32,3,63,0,2636841
18,Dalton Salvatore,54962,36,2,84,0,2616120
19,VoidL3ss,53793,80,1,194,0,2398303
20,Nakiriririri,52736,50,1,85,0,2469327
21,TaliMonk,52095,69,3,161,0,2351758
22,Jatix,51304,19,1,51,0,2518563
23,SunnieGal,45144,67,0,196,0,1991720
24,GhostWilliam,41805,26,1,103,0,1974355
25,kbaz,40818,40,2,58,0,1930282
26,Marropea,33661,30,4,79,0,1568580
27,OscarKid,31037,20,2,98,0,1452839
28,sunnieboy,31029,49,0,182,462493,1108595
29,G Maaaa,29814,36,2,80,0,1360746
30,Lord Morro,27947,28,2,63,0,1295872
31,Rotj,22927,16,2,118,0,1047353
32,grrinchy,21312,17,5,111,10445,962398
33,VANTAGAR,19898,17,4,48,0,928406
34,Senor Taco Man,18267,10,0,69,359655,673434
35,Jameszy,17684,6,0,71,0,833708
36,C4pitoshka,17358,2,2,70,552047,554212
37,Sir Candeez,16967,16,0,19,0,624352
38,Merkavar,16041,38,0,25,0,530974
39,MsBodie,15323,28,0,43,0,523402
40,VeEnaaa97,14173,7,0,34,0,674160
41,Chatz01,13788,13,1,90,234496,494698
42,Hasbullan,13130,8,3,75,0,610344
43,Felbeard,12988,8,3,124,418332,371002
44,555,9556,4,1,32,444908,229346
45,Neandre,9456,5,2,56,35794,414425
46,Zel0s,2709,8,1,10,0,110482
47,Ryzennn,0,0,0,0,0,0'''

    ladders = IrusLadder.from_csv(invasion_20240623, csv, members)
    month = IrusMonth.from_invasion_stats(month = 6, year = 2024)
    logger.debug(f'Month: {month}')

    yield month
    month.delete_from_table()
    invasion_20240611.delete_from_table()
    invasion_20240623.delete_from_table()
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


# todo: rename

# def foo_generate_report_202405(generate_report_202405):
#     assert generate_report_202405 is not None
#     logger.info(generate_report_202405.str())
#     logger.info(generate_report_202405.csv())

def test_generate_report_202406(generate_report_202406):
    assert generate_report_202406 is not None
    logger.info(generate_report_202406.str())
    logger.info(generate_report_202406.csv())

# def foo_generate_report_202406(generate_report_202405, generate_report_202406):
#     assert generate_report_202405 is not None
#     logger.info(generate_report_202405.str())
#     logger.info(generate_report_202405.csv())
#     assert generate_report_202406 is not None
#     logger.info(generate_report_202406.str())
#     logger.info(generate_report_202406.csv())

