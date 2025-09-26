import os
import boto3
import boto3.session
import pytest
from aws_lambda_powertools import Logger
from ..irus import IrusInvasion, IrusMember, IrusMemberList, IrusLadder

logger = Logger(service="test_irus_invasion", level="DEBUG", correlation_id=True)
profile = os.environ["AWS_PROFILE"]
session = boto3.session.Session(profile_name=profile)
dynamodb = session.resource("dynamodb")
table_name = os.environ["TABLE_NAME"]
table = dynamodb.Table(table_name)
s3 = session.resource("s3")
test_bucket_name = os.environ["TEST_BUCKET_NAME"]
test_bucket = s3.Bucket(test_bucket_name)
bucket_name = os.environ["BUCKET_NAME"]
bucket = s3.Bucket(bucket_name)


@pytest.fixture
def generate_first_ladder():
    invasion = IrusInvasion.from_user(
        day=11, month=6, year=2024, settlement="rw", win=True
    )
    logger.debug(f"Invasion {invasion}")

    Chatz01 = IrusMember.from_user(
        player="Chatz01",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    Stuggy = IrusMember.from_user(
        player="Stuggy",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=True,
    )
    members = IrusMemberList()

    ladder = IrusLadder.from_ladder_image(
        invasion, members, bucket_name, f"{invasion.path_ladders()}one.png"
    )
    logger.debug(f"Ladder {ladder}")

    yield ladder
    invasion.delete_from_table()
    ladder.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()


@pytest.fixture
def generate_fourth_ladder():
    invasion = IrusInvasion.from_user(
        day=11, month=6, year=2024, settlement="rw", win=True
    )
    logger.debug(f"Invasion {invasion}")

    Chatz01 = IrusMember.from_user(
        player="Chatz01",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    Stuggy = IrusMember.from_user(
        player="Stuggy",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=True,
    )
    Zel0s = IrusMember.from_user(
        player="Zel0s",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    SunnieGal = IrusMember.from_user(
        player="SunnieGal",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=False,
    )
    members = IrusMemberList()

    ladder = IrusLadder.from_ladder_image(
        invasion, members, bucket_name, f"{invasion.path_ladders()}four.png"
    )
    logger.debug(f"Ladder {ladder}")

    yield ladder
    invasion.delete_from_table()
    ladder.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()
    Zel0s.remove()
    SunnieGal.remove()


@pytest.fixture
def generate_invasion_ladders():
    invasion = IrusInvasion.from_user(
        day=11, month=6, year=2024, settlement="rw", win=True
    )
    logger.debug(f"Invasion {invasion}")

    Chatz01 = IrusMember.from_user(
        player="Chatz01",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    Stuggy = IrusMember.from_user(
        player="Stuggy",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=True,
    )
    Zel0s = IrusMember.from_user(
        player="Zel0s",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    SunnieGal = IrusMember.from_user(
        player="SunnieGal",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=False,
    )
    Merkavar = IrusMember.from_user(
        player="Merkavar",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    Fred = IrusMember.from_user(
        player="Fred",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )

    members = IrusMemberList()

    for f in [
        "one.png",
        "two.png",
        "three.png",
        "four.png",
        "five.png",
        "six.png",
        "seven.png",
        "eight.png",
    ]:
        ladder = IrusLadder.from_ladder_image(
            invasion, members, bucket_name, f"{invasion.path_ladders()}{f}"
        )
        logger.debug(f"Ladder {ladder}")

    ladders = IrusLadder.from_invasion(invasion)

    yield ladders
    invasion.delete_from_table()
    ladders.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()
    Zel0s.remove()
    SunnieGal.remove()
    Merkavar.remove()
    Fred.remove()


@pytest.fixture
def generate_roster():
    invasion = IrusInvasion.from_user(
        day=24, month=5, year=2024, settlement="bw", win=True
    )
    logger.debug(f"Invasion {invasion}")

    Chatz01 = IrusMember.from_user(
        player="Chatz01",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    Stuggy = IrusMember.from_user(
        player="Stuggy",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=True,
    )
    Zel0s = IrusMember.from_user(
        player="Zel0s",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    SunnieGal = IrusMember.from_user(
        player="SunnieGal",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=False,
    )
    GMaaa = IrusMember.from_user(
        player="G Maaaa",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=False,
    )
    members = IrusMemberList()

    roster = IrusLadder.from_roster_image(
        invasion,
        members,
        bucket_name,
        f"{invasion.path_roster()}20240524-bw-board-groups.png",
    )
    logger.debug(f"Roster {roster}")

    yield roster
    invasion.delete_from_table()
    roster.delete_from_table()
    Chatz01.remove()
    Stuggy.remove()
    Zel0s.remove()
    SunnieGal.remove()
    GMaaa.remove()


@pytest.fixture
def generate_large_one_ladder():
    invasion = IrusInvasion.from_user(
        day=23, month=6, year=2024, settlement="rw", win=True
    )
    logger.debug(f"Invasion {invasion}")

    SeaCoconut = IrusMember.from_user(
        player="Sea Coconut",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    TaliMonk = IrusMember.from_user(
        player="TaliMonk",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=True,
    )
    AbuHurayra = IrusMember.from_user(
        player="Abu Hurayra",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    Steve = IrusMember.from_user(
        player="Steve",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    LovingMum = IrusMember.from_user(
        player="Loving Mum",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    kbaz = IrusMember.from_user(
        player="kbaz",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=True,
    )
    SirCandeez = IrusMember.from_user(
        player="Sir Candeez",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    Julie = IrusMember.from_user(
        player="Julie",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )

    members = IrusMemberList()

    for f in ["20240623-rw.png"]:
        ladder = IrusLadder.from_ladder_image(
            invasion, members, bucket_name, f"{invasion.path_ladders()}{f}"
        )
        logger.debug(f"Ladder {ladder}")

    ladders = IrusLadder.from_invasion(invasion)

    yield ladders
    invasion.delete_from_table()
    ladders.delete_from_table()
    SeaCoconut.remove()
    AbuHurayra.remove()
    TaliMonk.remove()
    Steve.remove()
    LovingMum.remove()
    kbaz.remove()
    SirCandeez.remove()
    Julie.remove()


@pytest.fixture
def generate_large_six_ladders():
    invasion = IrusInvasion.from_user(
        day=23, month=6, year=2024, settlement="rw", win=True
    )
    logger.debug(f"Invasion {invasion}")

    SeaCoconut = IrusMember.from_user(
        player="Sea Coconut",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    TaliMonk = IrusMember.from_user(
        player="TaliMonk",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=True,
    )
    AbuHurayra = IrusMember.from_user(
        player="Abu Hurayra",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    Steve = IrusMember.from_user(
        player="Steve",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    LovingMum = IrusMember.from_user(
        player="Loving Mum",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    kbaz = IrusMember.from_user(
        player="kbaz",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=True,
    )
    SirCandeez = IrusMember.from_user(
        player="Sir Candeez",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    Julie = IrusMember.from_user(
        player="Julie",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )

    members = IrusMemberList()

    for f in ["one.png", "two.png", "three.png", "four.png", "five.png", "six.png"]:
        ladder = IrusLadder.from_ladder_image(
            invasion, members, bucket_name, f"{invasion.path_ladders()}{f}"
        )
        logger.debug(f"Ladder {ladder}")

    ladders = IrusLadder.from_invasion(invasion)

    yield ladders
    invasion.delete_from_table()
    ladders.delete_from_table()
    SeaCoconut.remove()
    AbuHurayra.remove()
    TaliMonk.remove()
    Steve.remove()
    LovingMum.remove()
    kbaz.remove()
    SirCandeez.remove()
    Julie.remove()


@pytest.fixture
def generate_from_csv():
    invasion = IrusInvasion.from_user(
        day=23, month=6, year=2024, settlement="rw", win=True
    )
    logger.debug(f"Invasion {invasion}")

    SeaCoconut = IrusMember.from_user(
        player="Sea Coconut",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    TaliMonk = IrusMember.from_user(
        player="TaliMonk",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=True,
    )
    AbuHurayra = IrusMember.from_user(
        player="Abu Hurayra",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    Steve = IrusMember.from_user(
        player="Steve",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    LovingMum = IrusMember.from_user(
        player="Loving Mum",
        day=1,
        month=5,
        year=2024,
        faction="purple",
        admin=False,
        salary=True,
    )
    kbaz = IrusMember.from_user(
        player="kbaz",
        day=1,
        month=5,
        year=2024,
        faction="green",
        admin=True,
        salary=True,
    )
    SirCandeez = IrusMember.from_user(
        player="Sir Candeez",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )
    Julie = IrusMember.from_user(
        player="Julie",
        day=1,
        month=5,
        year=2024,
        faction="yellow",
        admin=False,
        salary=True,
    )

    members = IrusMemberList()

    csv = """
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
47,Ryzennn,0,0,0,0,0,0
    """

    ladders = IrusLadder.from_csv(invasion, csv, members)

    yield ladders
    invasion.delete_from_table()
    ladders.delete_from_table()
    SeaCoconut.remove()
    AbuHurayra.remove()
    TaliMonk.remove()
    Steve.remove()
    LovingMum.remove()
    kbaz.remove()
    SirCandeez.remove()
    Julie.remove()


def test_generate_first_ladder(generate_first_ladder):
    assert generate_first_ladder is not None
    assert generate_first_ladder.invasion is not None
    logger.info(generate_first_ladder.csv())
    assert generate_first_ladder.count() == 8
    assert generate_first_ladder.members() == 2
    assert (
        generate_first_ladder.contiguous_from_1_until() == generate_first_ladder.count()
    )


def test_generate_fourth_ladder(generate_fourth_ladder):
    assert generate_fourth_ladder is not None
    assert generate_fourth_ladder.invasion is not None
    logger.info(generate_fourth_ladder.csv())
    assert generate_fourth_ladder.count() == 4
    assert generate_fourth_ladder.members() == 2
    assert (
        generate_fourth_ladder.contiguous_from_1_until()
        != generate_fourth_ladder.count()
        == 4
    )


def test_generate_invasion_ladders(generate_invasion_ladders):
    assert generate_invasion_ladders is not None
    assert generate_invasion_ladders.invasion is not None
    logger.info(generate_invasion_ladders.csv())
    assert generate_invasion_ladders.count() == 52
    assert generate_invasion_ladders.members() == 5
    assert (
        generate_invasion_ladders.contiguous_from_1_until()
        == generate_invasion_ladders.count()
    )


def test_generate_roster(generate_roster):
    assert generate_roster is not None
    assert generate_roster.invasion is not None
    logger.info(generate_roster.csv())
    assert generate_roster.count() == 4
    assert generate_roster.members() == 4
    assert generate_roster.contiguous_from_1_until() == generate_roster.count() == 4


def test_generate_large_one_ladder(generate_large_one_ladder):
    assert generate_large_one_ladder is not None
    assert generate_large_one_ladder.invasion is not None
    logger.info(generate_large_one_ladder.csv())
    assert (
        generate_large_one_ladder.count() == 46
        or generate_large_one_ladder.count() == 47
    )
    assert generate_large_one_ladder.members() == 6
    assert (
        generate_large_one_ladder.contiguous_from_1_until()
        == generate_large_one_ladder.count()
    )


def test_generate_large_six_ladders(generate_large_six_ladders):
    assert generate_large_six_ladders is not None
    assert generate_large_six_ladders.invasion is not None
    logger.info(generate_large_six_ladders.csv())
    assert (
        generate_large_six_ladders.count() == 46
        or generate_large_six_ladders.count() == 47
    )
    assert generate_large_six_ladders.members() == 6
    assert (
        generate_large_six_ladders.contiguous_from_1_until()
        == generate_large_six_ladders.count()
    )


def test_generate_from_csv(generate_from_csv):
    assert generate_from_csv is not None
    assert generate_from_csv.invasion is not None
    logger.info(generate_from_csv.csv())
    assert generate_from_csv.count() == 47
    assert generate_from_csv.members() == 6
    assert generate_from_csv.contiguous_from_1_until() == generate_from_csv.count()
