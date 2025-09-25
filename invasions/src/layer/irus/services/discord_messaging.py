"""Discord messaging service for posting tables and messages via webhooks."""

import json

from botocore.exceptions import ClientError

from ..container import IrusContainer


class DiscordMessagingService:
    """Service for sending messages to Discord via webhooks and step functions."""

    def __init__(self, container: IrusContainer | None = None):
        """Initialize the Discord messaging service.

        Args:
            container: Dependency injection container. Uses default if None.
        """
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._state_machine = self._container.state_machine()
        self._step_func_arn = self._container.post_step_function_arn()
        self._webhook_url = self._container.webhook_url()

    def post_table(
        self, channel_id: str, token: str, table_data: list[str], title: str
    ) -> str:
        """Post a table to Discord via step function workflow.

        Args:
            channel_id: Discord channel ID
            token: Discord bot token
            table_data: List of table rows as strings
            title: Title for the table

        Returns:
            Empty string on success, error message on failure
        """
        self._logger.info(f"Posting table '{title}' with {len(table_data)} rows")

        # Build command payload
        cmd = self._build_table_command(channel_id, token, table_data, title)

        # Log warning for large tables
        if cmd["count"] > 4:
            self._logger.warning(f"Too many posts ({cmd['count']}) for table '{title}'")

        # Execute step function
        return self._execute_post_workflow(cmd, title)

    def _build_table_command(
        self, channel_id: str, token: str, table_data: list[str], title: str
    ) -> dict:
        """Build the command payload for table posting.

        Args:
            channel_id: Discord channel ID
            token: Discord bot token
            table_data: List of table rows as strings
            title: Title for the table

        Returns:
            Command dictionary for step function
        """
        cmd = {
            "post": f"{self._webhook_url}/{channel_id}/{token}",
            "msg": [],
            "count": 0,
        }

        count = 1
        current_msg = title + "\n"

        # Split table into messages that fit Discord's character limit
        for row in table_data:
            formatted_row = f"`{row}`\n"

            # Check if adding this row would exceed Discord's limit (2000 chars)
            if len(current_msg) + len(formatted_row) > 1995:
                cmd["msg"].append(current_msg)
                current_msg = formatted_row
                count += 1
            else:
                current_msg += formatted_row

        # Add final message
        cmd["msg"].append(current_msg)
        cmd["count"] = count

        return cmd

    def _execute_post_workflow(self, cmd: dict, title: str) -> str:
        """Execute the step function workflow for posting.

        Args:
            cmd: Command payload for step function
            title: Title for logging purposes

        Returns:
            Empty string on success, error message on failure
        """
        self._logger.info(
            f"Starting step function for '{title}' with {len(cmd['msg'])} posts"
        )

        try:
            self._state_machine.start_execution(
                stateMachineArn=self._step_func_arn, input=json.dumps(cmd)
            )
            return ""

        except ClientError as e:
            error_msg = f"Failed to call post table step function: {e}"
            self._logger.warning(error_msg)
            return error_msg

    def post_simple_message(self, channel_id: str, token: str, message: str) -> str:
        """Post a simple message to Discord.

        Args:
            channel_id: Discord channel ID
            token: Discord bot token
            message: Message content

        Returns:
            Empty string on success, error message on failure
        """
        self._logger.info(f"Posting simple message to channel {channel_id}")

        cmd = {
            "post": f"{self._webhook_url}/{channel_id}/{token}",
            "msg": [message],
            "count": 1,
        }

        return self._execute_post_workflow(cmd, "simple message")
