from .environ import IrusResources
from .invasion import IrusInvasion

logger = IrusResources.logger()
s3 = IrusResources.s3()
bucket_name = IrusResources.bucket_name()

class IrusReport:

    def __init__(self, path: str, name: str, report:str):
        self.presigned : str = None
        self.target = path + name
        self.msg : str = None

        s3.Object(bucket_name, self.target).put(Body=report)
        self.presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': self.target}, ExpiresIn=3600)
        logger.info(f'IrusReport generated for {self.target}')
        logger.debug(self.presigned)
        self.msg = f"Report can be downloaded from **[here]({self.presigned})** for one hour."
    

    @classmethod
    def from_invasion(cls, invasion:IrusInvasion, report:str):
        logger.debug(f'IrusReport.from_invasion: {invasion}\n{report}')
        return cls(path = 'reports/invasion/', name = f'{invasion.name}.csv', report = report)

    @classmethod
    def from_month(cls, month:int, report:str):
        logger.debug(f'IrusReport.from_month: {month}\n{report}')
        return cls(path = 'reports/month/', name = f'{month}.csv', report = report)

    @classmethod
    def from_members(cls, timestamp:int, report:str):
        logger.debug(f'IrusReport.from_members: {timestamp}\n{report}')
        return cls(path = 'reports/members/', name = f'{timestamp}.csv', report = report)

