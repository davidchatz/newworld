from boto3.dynamodb.conditions import Key
from dataclasses import dataclass
from .member import IrusMember
from .environ import IrusResources

logger = IrusResources.logger()
table = IrusResources.table()

class IrusMemberList:

    def __init__(self):
        logger.info(f'MemberList.__init__')

        self.members = []

        response = table.query(KeyConditionExpression=Key('invasion').eq('#member'))
        logger.debug(response)

        if not response.get('Items', None):
            logger.info(f'No members found')
        else:
            items = response["Items"]
            for i in items:
                self.members.append(IrusMember(i))

    def str(self) -> str:
        return f'MemberList(count={len(self.members)})'
    
    def csv(self) -> str:
        body = f"player,faction,start\n"
        for m in self.members:
            body += f'{m.player},{m.faction},{m.start}\n'
        return body

    def markdown(self) -> str:
        body = f"# {len(self.members)} Members\n"
        body += "*Note: This list may be truncated, run **report members** to get full list.*\n"
        for m in self.members:
            body += '- f{m.player} ({m.faction}) started {m.start}\n'
        return body

    def count(self) -> int:
        return len(self.members)
    
    def get(self,index:int) -> IrusMember:
        return self.members[index]
    
    # Returns name of player matched, else None
    def is_member(self, player:str, partial:bool = False) -> str:
        # Replace any letter O in name with number 0
        playerO = player.replace('O', '0')
        # Replace any number 0 in name with letter 0
        player0 = playerO.replace('0', 'O')

        # Check if player is in the list
        for m in self.members:
            if m.player == player or m.player == playerO or m.player == player0:
                return m.player
            # Roster text scan can struggle with some names, especially multi-word names
            if partial and (m.player.startswith(player) or m.player.startswith(playerO) or m.player.startswith(player0)):
                return m.player
        return None

        #     filename = f'members/{date}.csv'
        #     logger.info(f'Writing member list to {bucket_name}/{filename}')
        #     s3_resource.Object(bucket_name, filename).put(Body=body)

        #     print(f'Generating presigned URL for {filename}')
        #     try:
        #         presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': filename}, ExpiresIn=3600)
        #         mesg = f'# {len(items)} Members\nDownload the report (for 1 hour) from **[here]({presigned})**'
        #     except ClientError as e:
        #         print(e)
        #         mesg = f'Error generating presigned URL for {filename}: {e}'

        # return mesg
