from decimal import Decimal

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from .container import IrusContainer
from .invasionlist import IrusInvasionList
from .memberlist import IrusMemberList
from .repositories.ladder import LadderRepository

prec = Decimal("1.0")


class IrusMonth:
    """Service for generating monthly invasion statistics and reports."""

    def __init__(
        self,
        month: str,
        invasions: int,
        report: list,
        names: list,
        container: IrusContainer | None = None,
    ):
        """Initialize monthly report with calculated statistics.

        Args:
            month: Month identifier (e.g., '202406')
            invasions: Number of invasions in the month
            report: List of member statistics dictionaries
            names: List of invasion names in the month
            container: Optional container for dependencies
        """
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()

        self._logger.info(f"IrusMonth.__init__: {month}")
        self.report = report
        self.month = month
        self.invasions = invasions
        self.names = names
        self.participation = 0
        self.active = 0

        # Calculate statistics from report data
        for r in report:
            self._logger.debug(
                f"IrusMonth.__init__: {r['id']} {r['wins']} {r['salary']} {self.participation}"
            )
            if r["salary"]:
                self.participation += r["wins"]
            if r["invasions"] > 0:
                self.active += 1

    def invasion_key(self) -> str:
        return f"#month#{self.month}"

    @classmethod
    def from_invasion_stats(
        cls, month: int, year: int, container: IrusContainer | None = None
    ):
        """Generate monthly statistics from invasion data using repository pattern.

        Args:
            month: Month number (1-12)
            year: Year (e.g., 2024)
            container: Optional container for dependencies

        Returns:
            IrusMonth instance with calculated member statistics
        """
        container = container or IrusContainer.default()
        logger = container.logger()
        ladder_repository = LadderRepository(container)

        logger.info(f"IrusMonth.from_invasion_stats: {month}/{year}")

        date = f"{year}{month:02d}"
        invasions = IrusInvasionList.from_month(month, year, container)
        members = IrusMemberList(container)

        if invasions.count() == 0:
            logger.info(f"Note no invasions found for {date}")

        if members.count() == 0:
            logger.info("Note no members found")

        report = []
        initial = {
            "invasion": f"#month#{date}",
            "id": "initial",
            "salary": Decimal(0),
            "invasions": Decimal(0),
            "ladders": Decimal(0),
            "wins": Decimal(0),
            "sum_score": 0,
            "sum_kills": 0,
            "sum_assists": 0,
            "sum_deaths": 0,
            "sum_heals": 0,
            "sum_damage": 0,
            "avg_score": Decimal(0.0),
            "avg_kills": Decimal(0.0),
            "avg_assists": Decimal(0.0),
            "avg_deaths": Decimal(0.0),
            "avg_heals": Decimal(0.0),
            "avg_damage": Decimal(0.0),
            "avg_rank": Decimal(0.0),
            "max_score": Decimal(0.0),
            "max_kills": Decimal(0.0),
            "max_assists": Decimal(0.0),
            "max_deaths": Decimal(0.0),
            "max_heals": Decimal(0.0),
            "max_damage": Decimal(0.0),
            "max_rank": Decimal(100.0),
        }
        for i in invasions.range():
            invasion = invasions.get(i)
            initial[invasion.name] = "-"

        logger.info(f"IrusMonth.from_invasion_stats initial: {initial}")

        for m in members.range():
            member = members.get(m)
            logger.debug(
                f"IrusMonth.from_invasion_stats: Adding {member.player} {member.salary}"
            )
            initial["id"] = member.player
            initial["salary"] = member.salary
            report.append(initial.copy())

        names = []
        for i in invasions.range():
            invasion = invasions.get(i)
            names.append(invasion.name)
            # Use repository to get ladder data for this invasion
            ladder = ladder_repository.get_ladder(invasion.name)

            if not ladder:
                logger.warning(
                    f"No ladder found for invasion {invasion.name}, skipping"
                )
                continue

            for r in report:
                rank = ladder.member(r["id"])
                logger.debug(
                    f"IrusMonth.from_invasion_stats: Matching {r['id']} {invasion.name} {rank}"
                )
                if rank:
                    r["invasions"] += 1
                    if invasion.win:
                        r["wins"] += 1
                        r[invasion.name] = "W"
                    else:
                        r[invasion.name] = "L"
                    if rank.ladder:
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
                        logger.debug(
                            f"Skipping stats for {r['id']} from non-ladder invasion {invasion.name}"
                        )

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

        logger.debug(f"Computed report for {date}: {report}")

        # Save monthly report data to database using container
        table = container.table()
        count = 0
        with table.batch_writer() as batch:
            for r in report:
                if r["invasions"] > 0:
                    count += 1
                    batch.put_item(Item=r)

        logger.info(f"Saved {count} member reports for {date}")

        return cls(date, invasions.count(), report, names, container)

    @classmethod
    def from_table(cls, month: int, year: int, container: IrusContainer | None = None):
        """Load monthly report from database.

        Args:
            month: Month number (1-12)
            year: Year (e.g., 2024)
            container: Optional container for dependencies

        Returns:
            IrusMonth instance with data loaded from database

        Raises:
            ValueError: If no data found for the specified month
        """
        container = container or IrusContainer.default()
        logger = container.logger()
        table = container.table()

        logger.info(f"IrusMonth.from_table: {month}/{year}")

        zero_month = f"{month:02d}"
        date = f"{year}{zero_month}"

        response = table.query(
            KeyConditionExpression=Key("invasion").eq(f"#month#{date}"),
            Select="ALL_ATTRIBUTES",
        )

        if response["Count"] == 0:
            logger.info(f"Note no data found for month {date}")
            raise ValueError(f"Note no data found for month {date}")

        invasions = table.query(
            KeyConditionExpression=Key("invasion").eq("#invasion")
            & Key("id").begins_with(date),
            Select="ALL_ATTRIBUTES",
        )

        logger.info(f"IrusMonth.from_table: {invasions}")
        inv_count = invasions["Count"]
        names = []
        if inv_count > 0:
            for i in invasions["Items"]:
                names.append(i["id"])

        report = response["Items"]
        logger.debug(
            f"Retrieved report for {date} based on {inv_count} invasions: {names}"
        )

        return cls(
            month=date,
            invasions=inv_count,
            report=report,
            names=names,
            container=container,
        )

    def str(self) -> str:
        mesg = f"# Monthly report for {self.month}\n"
        mesg += f"- Invasions: {self.invasions}\n"
        mesg += f"- Active Members (1 or more invasions): {self.active} of {len(self.report)}\n"
        mesg += f"- Participation (sum of members across invasions won): {self.participation}\n"
        return mesg

    def csv(self) -> str:
        body = "month,name,salary,invasions,wins,sum_score,sum_kills,sum_assists,sum_deaths,sum_heals,sum_damage,avg_score,avg_kills,avg_assists,avg_deaths,avg_heals,avg_damage,avg_ranks,max_score,max_kills,max_assists,max_deaths,max_heals,max_damage,max_rank\n"
        for r in self.report:
            if r["invasions"] > 0:
                body += f"{self.month},{r['id']},{r['salary']},{r['invasions']},{r['wins']},{r['sum_score']},{r['sum_kills']},{r['sum_assists']},{r['sum_deaths']},{r['sum_heals']},{r['sum_damage']},{r['avg_score']},{r['avg_kills']},{r['avg_assists']},{r['avg_deaths']},{r['avg_heals']},{r['avg_damage']},{r['avg_rank']},{r['max_score']},{r['max_kills']},{r['max_assists']},{r['max_deaths']},{r['max_heals']},{r['max_damage']},{r['max_rank']}\n"
        self._logger.debug(f"csv: {body}")
        return body

    # improve csv output that has less stats but maps all the invasions in the month
    def csv2(self, gold: int) -> str:
        body = "month,name,payment,invasions,wins,avg_score,avg_kills,avg_assists,avg_deaths,avg_heals,avg_damage,avg_ranks"
        mapping = f"{self.month},"
        mapping += "{id},{payment},{invasions},{wins},{avg_score},{avg_kills},{avg_assists},{avg_deaths},{avg_heals},{avg_damage},{avg_rank}"

        # invasions = IrusInvasionList.from_month(month = int(self.month[4:]), year = int(self.month[:4]))
        # for i in invasions.range():
        #     invasion = invasions.get(i)
        #     body += f',{invasion.name[6:]}'
        #     mapping += ',{' + f'{invasion.name}' + '}'
        # body += '\n'

        for n in self.names:
            body += f",{n[6:]}"
            mapping += ",{" + f"{n}" + "}"
        body += "\n"

        self._logger.debug(f"csv2 body: {body}")
        self._logger.debug(f"csv2 mapping: {mapping}")

        for r in self.report:
            if r["invasions"] > 0:
                if gold > 0 and r["salary"]:
                    r["payment"] = round((r["wins"] * gold) / self.participation, 0)
                else:
                    r["payment"] = 0
                body += mapping.format(**r)
                body += "\n"
        self._logger.debug(f"csv: {body}")
        return body

    def post(self) -> list:
        mesg = [
            "month player            salary invasions wins sum_score sum_kills sum_assists sum_deaths sum_heals sum_damage avg_score avg_kills avg_assists avg_deaths avg_heals avg_damage avg_ranks max_score max_kills max_assists max_deaths max_heals max_damage max_rank"
        ]
        for r in self.report:
            if r["invasions"] > 0:
                mesg.append(
                    f"{self.month} {r['id']:<16} {r['salary']:>6} {r['invasions']:>9} {r['wins']:>4} {r['sum_score']:>9} {r['sum_kills']:>9} {r['sum_assists']:>11} {r['sum_deaths']:>10} {r['sum_heals']:>9} {r['sum_damage']:>10} {r['avg_score']:>9} {r['avg_kills']:>9} {r['avg_assists']:>11} {r['avg_deaths']:>10} {r['avg_heals']:>9} {r['avg_damage']:>10} {r['avg_rank']:>9} {r['max_score']:>9} {r['max_kills']:>9} {r['max_assists']:>11} {r['max_deaths']:>10} {r['max_heals']:>9} {r['max_damage']:>10} {r['max_rank']:>8}"
                )
        return mesg

    def post2(self, gold: int) -> list:
        header = "player           payment inv wins     score kills assist deaths     heals     damage rank"
        mapping = "{id:<16} {payment:>7} {invasions:>3} {wins:>4} {avg_score:>9} {avg_kills:>5} {avg_assists:>6} {avg_deaths:>6} {avg_heals:>9} {avg_damage:>10} {avg_rank:>4}"

        # invasions = IrusInvasionList.from_month(month = int(self.month[4:]), year = int(self.month[:4]))
        # for i in invasions.range():
        #     invasion = invasions.get(i)
        #     header += f' {invasion.name[6:8]}{invasion.name[9:11]}'
        #     mapping += '   {' + f'{invasion.name}' + '} '

        for n in self.names:
            header += f" {n[6:8]}{n[9:11]}"
            mapping += "   {" + f"{n}" + "} "

        mesg = [header]
        for r in self.report:
            if r["invasions"] > 0:
                if gold > 0 and r["salary"]:
                    r["payment"] = round((r["wins"] * gold) / self.participation, 0)
                else:
                    r["payment"] = 0
                mesg.append(mapping.format(**r))
        return mesg

    def delete_from_table(self):
        self._logger.info(f"IrusMonth.delete_from_table for month {self.month}")
        table = self._container.table()

        try:
            with table.batch_writer() as batch:
                for r in self.report:
                    if r["invasions"] > 0:
                        batch.delete_item(
                            Key={"invasion": r["invasion"], "id": r["id"]}
                        )
        except ClientError as err:
            self._logger.error("Failed to delete from table: %s", err)
            raise ValueError("Failed to delete from table") from err

    def member(self, player: str) -> dict:
        for r in self.report:
            self._logger.debug(f"IrusMonth.member: Checking {r['id']} against {player}")
            if r["id"] == player:
                return r
        return None

    def member_stats(self, player: str) -> str:
        item = self.member(player)
        if item:
            mesg = f"## Stats for {self.month}\n"
            mesg += "Invasion Wins: {wins} of {invasions}\n".format_map(item)

            for n in self.names:
                if n in item and item[n] == "W":
                    mesg += f"- {n}\n"

            mesg += "`                Sum /        Max /    Average`\n"
            mesg += "`Score:   {sum_score:>10} / {max_score:>10} / {avg_score:>10}`\n".format_map(
                item
            )
            mesg += "`Kills:   {sum_kills:>10} / {max_kills:>10} / {avg_kills:>10}`\n".format_map(
                item
            )
            mesg += "`Assists: {sum_assists:>10} / {max_assists:>10} / {avg_assists:>10}`\n".format_map(
                item
            )
            mesg += "`Deaths:  {sum_deaths:>10} / {max_deaths:>10} / {avg_deaths:>10}`\n".format_map(
                item
            )
            mesg += "`Heals:   {sum_heals:>10} / {max_heals:>10} / {avg_heals:>10}`\n".format_map(
                item
            )
            mesg += "`Damage:  {sum_damage:>10} / {max_damage:>10} / {avg_damage:>10}`\n".format_map(
                item
            )
        else:
            mesg = f"*No stats found for {player} in {self.month}*\n"

        return mesg

    def member_line_header() -> str:
        return "month  invasions wins avg_score avg_kills avg_assists avg_deaths avg_heals avg_damage avg_rank max_score max_kills max_assists max_deaths max_heals max_damage max_rank"

    def member_line(self, player: str) -> str:
        item = self.member(player)
        mesg = f"{self.month}         0"
        if item:
            mesg = f"{self.month} {item['invasions']:>9} {item['wins']:>4} {item['avg_score']:>9} {item['avg_kills']:>9} {item['avg_assists']:>11} {item['avg_deaths']:>10} {item['avg_heals']:>9} {item['avg_damage']:>10} {item['avg_rank']:>8} {item['max_score']:>9} {item['max_kills']:>9} {item['max_assists']:>11} {item['max_deaths']:>10} {item['max_heals']:>9} {item['max_damage']:>10} {item['max_rank']:>8}"
        return mesg
