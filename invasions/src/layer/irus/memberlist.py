from .container import IrusContainer
from .models.member import IrusMember
from .repositories.member import MemberRepository


class IrusMemberList:
    """Collection class for managing all members."""

    def __init__(self, container: IrusContainer | None = None):
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._repository = MemberRepository(container)

        self._logger.info("MemberList.__init__")

        # Load all members using repository
        self.members = self._repository.get_all()

        if not self.members:
            self._logger.info("No members found")
        else:
            self._logger.debug(f"Loaded {len(self.members)} members")

    def str(self) -> str:
        return f"MemberList(count={len(self.members)})"

    def csv(self) -> str:
        body = "player,faction,start\n"
        for f in ["green", "purple", "yellow"]:
            for m in self.members:
                if m.faction == f:
                    body += f"{m.player},{m.faction},{m.start}\n"
        return body

    def markdown(self, faction: str = None) -> str:
        if faction is None:
            body = "# Member List\n"
        else:
            body = f"# Member List for {faction}\n"

        body += "*Note: This list may be truncated if too long, run **report members** if count not shown.*\n"
        count = 0

        for f in ["green", "purple", "yellow"]:
            if faction is not None and f != faction:
                continue
            for m in self.members:
                if m.faction != f:
                    continue
                body += f"- {m.player} ({m.faction}) started {m.start}\n"
                count += 1
        body += f"\nCount: {count}\n"

        return body

    def post(self, faction: str = None) -> list:
        msg = ["Player         Faction Start"]
        count = 0
        for f in ["green", "purple", "yellow"]:
            if faction is not None and f != faction:
                continue
            for m in self.members:
                if m.faction != f:
                    continue
                msg.append(f"{m.player:<14} {m.faction:<7} {m.start}")
                count += 1
        msg.append(" ")
        if faction is None:
            msg.append(f"{count} members in clan.")
        else:
            msg.append(f"{count} members in clan for faction {faction}.")
        return msg

    def count(self) -> int:
        return len(self.members)

    def range(self) -> range:
        return range(0, len(self.members))

    def get(self, index: int) -> IrusMember:
        return self.members[index]

    # Returns name of player matched, else None
    def is_member(self, player: str, partial: bool = False) -> str:
        # Replace any letter O in name with number 0
        player_o = player.replace("O", "0")
        # Replace any number 0 in name with letter 0
        player_0 = player_o.replace("0", "O")

        # Check if player is in the list
        for m in self.members:
            if m.player == player or m.player == player_o or m.player == player_0:
                return m.player
            # Roster text scan can struggle with some names, especially multi-word names
            if partial and (
                m.player.startswith(player)
                or m.player.startswith(player_o)
                or m.player.startswith(player_0)
            ):
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
