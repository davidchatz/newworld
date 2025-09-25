import json

from botocore.exceptions import ClientError

from .container import IrusContainer
from .models.invasion import IrusInvasion


class IrusFiles:
    """File collection for Discord attachments processing."""

    def __init__(self, container: IrusContainer | None = None):
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self.files: list = []

    def append(self, name: str, attachment: str):
        """Add a file to the collection."""
        self._logger.debug(f"Files.append: {name} {attachment}")
        self.files.append({"name": name, "attachment": attachment})

    def update(self, attachments: dict):
        """Update files with attachment metadata from Discord."""
        self._logger.debug(f"Attachments: {attachments}")
        for a in self.files:
            a["filename"] = attachments[a["attachment"]]["filename"]
            a["url"] = attachments[a["attachment"]]["url"]
        self._logger.debug(f"Files: {self.files}")
        for a in self.files:
            if "filename" not in a:
                self._logger.warning(f"Missing filename for {a['name']}")
                raise ValueError(f"Missing filename for {a['name']}")

    def get(self) -> list:
        """Get the list of files."""
        return self.files

    def str(self) -> str:
        """Get string representation of file count."""
        return f"{len(self.files)} files"


class IrusProcess:
    """Service for managing invasion screenshot processing workflows."""

    def __init__(self, container: IrusContainer | None = None):
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._step_machine = self._container.state_machine()
        self.step_func_arn = self._container.process_step_function_arn()
        self.webhook_url = self._container.webhook_url()

    def start(
        self,
        id: str,
        token: str,
        invasion: IrusInvasion,
        files: IrusFiles,
        process: str,
    ) -> str:
        """Start the invasion screenshot processing workflow.

        Args:
            id: Discord interaction ID
            token: Discord interaction token
            invasion: Invasion model containing metadata
            files: Collection of Discord attachments to process
            process: Processing type ("Ladder" or "Roster")

        Returns:
            Status message indicating workflow started or error details
        """
        self._logger.info(
            f"Process.start: invasion: {invasion.name} files: {files.str()} process: {process}"
        )

        cmd = {
            "post": f"{self.webhook_url}/{id}/{token}",
            "invasion": invasion.name,
            "folder": "tbd",
            "files": files.get(),
            "process": process,
            "month": invasion.month_prefix(),
        }

        if process == "Ladder":
            cmd["folder"] = invasion.path_ladders()
        elif process == "Roster":
            cmd["folder"] = invasion.path_roster()
        else:
            raise ValueError(f"invasion_screenshots: Unknown process {process}")

        self._logger.info(f"starting process with: {cmd}")

        try:
            self._step_machine.start_execution(
                stateMachineArn=self.step_func_arn, input=json.dumps(cmd)
            )

        except ClientError as e:
            self._logger.warning(f"Failed to call process step function: {e}")
            return f"Failed to call process step function: {e}"

        return "In Progress: Downloading and processing screenshot(s)"
