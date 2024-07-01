from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from dataclasses import dataclass
from datetime import datetime
from .environ import IrusResources
from .invasion import IrusInvasion
from .invasionlist import IrusInvasionList
from .memberlist import IrusMemberList
from .ladder import IrusLadder

logger = IrusResources.logger()
table = IrusResources.table()

from decimal import Decimal, getcontext
prec = Decimal("1.0")


class IrusMonth:

    def __init__(self, month: str, invasions: int, report:list):
        logger.info(f'IrusMonth.__init__: {month}')
        self.report = report
        self.month = month
        self.invasions = invasions
        self.participation = 0
        for r in report:
            logger.info(f'IrusMonth.__init__: {r["id"]} {r["wins"]} {r["salary"]} {self.participation}')
            if r["salary"] == True:
                self.participation += r["wins"]


    def invasion_key(self) -> str:
        return f'#month#{self.month}'

    @classmethod
    def from_invasion_stats(cls, month:int, year:int):
        logger.info(f'IrusMonth.from_invasion_stats: {month}/{year}')

        date = f'{year}{month:02d}'
        invasions = IrusInvasionList.from_month(month, year)
        members = IrusMemberList()
        
        if invasions.count() == 0:
            logger.info(f'Note no invasions found for {date}')

        if members.count() == 0:
            logger.info(f'Note no members found')

        report = []
        for m in members.range():
            member = members.get(m)
            logger.debug(f'IrusMonth.from_invasion_stats: Adding {member.player} {member.salary}')
            report.append({'invasion': f'#month#{date}', 'id': member.player, 'salary': member.salary, 'invasions': Decimal(0), 'ladders': Decimal(0), 'wins': Decimal(0),
                            'sum_score': 0, 'sum_kills': 0, 'sum_assists': 0, 'sum_deaths': 0, 'sum_heals': 0, 'sum_damage': 0,
                            'avg_score': Decimal(0.0), 'avg_kills': Decimal(0.0), 'avg_assists': Decimal(0.0), 'avg_deaths': Decimal(0.0), 'avg_heals': Decimal(0.0), 'avg_damage': Decimal(0.0), 'avg_rank': Decimal(0.0),
                            'max_score': Decimal(0.0), 'max_kills': Decimal(0.0), 'max_assists': Decimal(0.0), 'max_deaths': Decimal(0.0), 'max_heals': Decimal(0.0), 'max_damage': Decimal(0.0), 'max_rank': Decimal(100.0)
                        })

        for i in invasions.range():
            invasion = invasions.get(i)
            ladder = IrusLadder.from_invasion(invasion)

            for r in report:
                rank = ladder.member(r["id"])
                logger.debug(f'IrusMonth.from_invasion_stats: Matching {r["id"]} {invasion.name} {rank}')
                if rank:
                    r["invasions"] += 1
                    if invasion.win == True:
                        r["wins"] += 1
                    if rank.ladder == True:
                        r["ladders"] += 1
                        r["sum_score"] += rank.score
                        r["sum_kills"] += rank.kills
                        r["sum_assists"] += rank.assists
                        r["sum_deaths"] += rank.deaths
                        r["sum_heals"] += rank.heals
                        r["sum_damage"] += rank.damage
                        r["avg_rank"] += Decimal(rank.rank)
                        r["max_score"] = max(r["max_score"], rank.score)
                        r["max_kills"] = max(r["max_kills"], rank.kills)
                        r["max_assists"] = max(r["max_assists"], rank.assists)
                        r["max_deaths"] = max(r["max_deaths"], rank.deaths)
                        r["max_heals"] = max(r["max_heals"], rank.heals)
                        r["max_damage"] = max(r["max_damage"], rank.damage)
                        r["max_rank"] = min(r["max_rank"], Decimal(rank.rank))
                    else:
                        logger.debug(f'Skipping stats for {r["id"]} from non-ladder invasion {invasion.name}')

        # compute averages
        for r in report:
            if r["ladders"] > 0:
                r["avg_score"] = (r["sum_score"] / r["ladders"]).quantize(prec)
                r["avg_kills"] = (r["sum_kills"] / r["ladders"]).quantize(prec)
                r["avg_assists"] = (r["sum_assists"] / r["ladders"]).quantize(prec)
                r["avg_deaths"] = (r["sum_deaths"] / r["ladders"]).quantize(prec)
                r["avg_heals"] = (r["sum_heals"] / r["ladders"]).quantize(prec)
                r["avg_damage"] = (r["sum_damage"] / r["ladders"]).quantize(prec)
                r["avg_rank"] /= r["ladders"]
                r["avg_rank"] = r["avg_rank"].quantize(prec)

        logger.debug(f'Computed report for {date}: {report}')

        count = 0
        with table.batch_writer() as batch:
            for r in report:
                if r["invasions"] > 0:
                    count += 1
                    batch.put_item(Item=r)

        return cls(date, invasions.count(), report)
    

    @classmethod
    def from_table(cls, month:int, year:int):
        logger.info(f'IrusMonth.from_table: {month}/{year}')

        zero_month = '{0:02d}'.format(month)
        date = f'{year}{zero_month}'

        response = table.query(
            KeyConditionExpression=Key('invasion').eq(f'#month#{month}'),
            Select='ALL_ATTRIBUTES'
        )
        report = response['Items']

        logger.debug(f'Retrieved report for {date}: {report}')

        return cls(date, report)


    def str(self) -> str:
        mesg = f'# Monthly report for {self.month}'
        mesg += f'- Invasions: {self.invasions}\n'
        mesg += f'- Active Members (1 or more invasions): {len(self.report)}\n'
        mesg += f'- Participation (sum of members across invasions won): {self.participation}\n'
        return mesg

    def csv(self) -> str:
        body = 'month,name,salary,invasions,ladders,wins,sum_score,sum_kills,sum_assists,sum_deaths,sum_heals,sum_damage,avg_score,avg_kills,avg_assists,avg_deaths,avg_heals,avg_damage,avg_ranks,max_score,max_kills,max_assists,max_deaths,max_heals,max_damage,max_rank\n'
        for r in self.report:
            if r["invasions"] > 0:
                body += f'{self.month},{r["id"]},{r["salary"]},{r["invasions"]},{r["ladders"]},{r["wins"]},{r["sum_score"]},{r["sum_kills"]},{r["sum_assists"]},{r["sum_deaths"]},{r["sum_heals"]},{r["sum_damage"]},{r["avg_score"]},{r["avg_kills"]},{r["avg_assists"]},{r["avg_deaths"]},{r["avg_heals"]},{r["avg_damage"]},{r["avg_rank"]},{r["max_score"]},{r["max_kills"]},{r["max_assists"]},{r["max_deaths"]},{r["max_heals"]},{r["max_damage"]},{r["max_rank"]}\n'
        logger.debug(f'csv: {body}')
        return body
    
    def delete_from_table(self):
        logger.info(f'IrusMonth.delete_from_table for month {self.month}')

        try:
            with table.batch_writer() as batch:
                for r in self.report:
                    if r["invasions"] > 0:
                        batch.delete_item(Key={'invasion': r["invasion"], 'id': r["id"]})
        except ClientError as err:
            logger.error(f'Failed to delete from table: {err}')
            raise ValueError(f'Failed to delete from table: {err}')