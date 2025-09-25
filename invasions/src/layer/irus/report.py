# Forward reference for IrusMonth to avoid circular imports
from typing import TYPE_CHECKING

from .container import IrusContainer
from .models.ladder import IrusLadder

if TYPE_CHECKING:
    from .month import IrusMonth


class IrusReport:
    """Service for generating and uploading reports to S3."""

    def __init__(
        self, path: str, name: str, report: str, container: IrusContainer | None = None
    ):
        """Initialize report and upload to S3.

        Args:
            path: S3 key path prefix (e.g., 'reports/invasion/')
            name: Report filename (e.g., 'invasion_name.csv')
            report: Report content as string
            container: Optional container for dependencies
        """
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._s3 = self._container.s3()
        self._bucket_name = self._container.bucket_name()

        self.presigned: str = None
        self.target = path + name
        self.msg: str = None

        # Upload report to S3
        self._s3.put_object(Bucket=self._bucket_name, Key=self.target, Body=report)

        # Generate presigned URL for download
        self.presigned = self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket_name, "Key": self.target},
            ExpiresIn=3600,
        )

        self._logger.info(f"IrusReport generated for {self.target}")
        self._logger.debug(self.presigned)
        self.msg = (
            f"Report can be downloaded from **[here]({self.presigned})** for one hour."
        )

    @classmethod
    def from_invasion(cls, ladder: IrusLadder, container: IrusContainer | None = None):
        """Create report from invasion ladder data.

        Args:
            ladder: IrusLadder model with invasion data and ranks
            container: Optional container for dependencies

        Returns:
            IrusReport instance with uploaded CSV report
        """
        container = container or IrusContainer.default()
        logger = container.logger()

        logger.debug(f"IrusReport.from_invasion: {ladder.invasion.name}")
        return cls(
            path="reports/invasion/",
            name=f"{ladder.invasion.name}.csv",
            report=ladder.csv(),
            container=container,
        )

    @classmethod
    def from_members(
        cls, timestamp: int, report: str, container: IrusContainer | None = None
    ):
        """Create report from member data.

        Args:
            timestamp: Unix timestamp for report filename
            report: CSV content as string
            container: Optional container for dependencies

        Returns:
            IrusReport instance with uploaded CSV report
        """
        container = container or IrusContainer.default()
        logger = container.logger()

        logger.debug(f"IrusReport.from_members: {timestamp}\n{report}")
        return cls(
            path="reports/members/",
            name=f"{timestamp}.csv",
            report=report,
            container=container,
        )

    @classmethod
    def from_month(
        cls, month: "IrusMonth", gold: int, container: IrusContainer | None = None
    ):
        """Create report from monthly invasion stats.

        Args:
            month: IrusMonth model with monthly data
            gold: Gold amount for calculations
            container: Optional container for dependencies

        Returns:
            IrusReport instance with uploaded CSV report
        """
        container = container or IrusContainer.default()
        logger = container.logger()

        logger.debug(f"IrusReport.from_month: {month.month}")
        return cls(
            path="reports/month/",
            name=f"{month.month}.csv",
            report=month.csv2(gold),
            container=container,
        )

    # @classmethod
    # def from_year(cls, year:int, member:str):
    #     logger.debug(f'IrusReport.from_year: {year}\n{member}')
    #     report = ''
    #     for m in range(1, 12):
    #         try:
    #             month = IrusMonth.from_table(month = m, year = year)
    #         except ValueError as e:
    #             logger.error(f'No results for month {m} in year {year}, skipping')
    #         report += month.member_stats(member)

    #     return cls(path = 'reports/members/', name = f'{year}.csv', report = report)
