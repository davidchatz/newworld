from .environ import IrusResources
from .ladder import IrusLadder
from .month import IrusMonth

logger = IrusResources.logger()
s3 = IrusResources.s3()
bucket_name = IrusResources.bucket_name()

class IrusReport:

    def __init__(self, path: str, name: str, report:str):
        self.presigned : str = None
        self.target = path + name
        self.msg : str = None

        s3.put_object(Bucket=bucket_name, Key=self.target, Body=report)
        self.presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': self.target}, ExpiresIn=3600)
        logger.info(f'IrusReport generated for {self.target}')
        logger.debug(self.presigned)
        self.msg = f"Report can be downloaded from **[here]({self.presigned})** for one hour."
    

    @classmethod
    def from_invasion(cls, ladder:IrusLadder):
        logger.debug(f'IrusReport.from_invasion: {ladder.invasion.name}')
        return cls(path = 'reports/invasion/', name = f'{ladder.invasion.name}.csv', report = ladder.csv())

    @classmethod
    def from_month(cls, month:IrusMonth):
        logger.debug(f'IrusReport.from_month: {month.month}')
        return cls(path = 'reports/month/', name = f'{month.month}.csv', report = month.csv())

    @classmethod
    def from_members(cls, timestamp:int, report:str):
        logger.debug(f'IrusReport.from_members: {timestamp}\n{report}')
        return cls(path = 'reports/members/', name = f'{timestamp}.csv', report = report)
