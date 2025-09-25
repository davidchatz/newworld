"""Backward compatibility facade for IrusPostTable.

This module provides backward compatibility for the legacy IrusPostTable class
while internally using the new DiscordMessagingService architecture.

DEPRECATED: This facade is provided for backward compatibility only.
New code should use irus.services.discord_messaging.DiscordMessagingService directly.
"""

import warnings

from .services.discord_messaging import DiscordMessagingService

# Issue deprecation warning when this module is imported
warnings.warn(
    "irus.posttable module is deprecated. Use irus.services.discord_messaging.DiscordMessagingService instead.",
    DeprecationWarning,
    stacklevel=2,
)


class IrusPostTable:
    """Legacy IrusPostTable class for backward compatibility.

    This class wraps the new DiscordMessagingService implementation to maintain
    backward compatibility with existing code.

    DEPRECATED: Use irus.services.discord_messaging.DiscordMessagingService instead.
    """

    def __init__(self) -> None:
        """Initialize the legacy post table class.

        Creates an instance of the new DiscordMessagingService internally.
        """
        self._service = DiscordMessagingService()

    def start(self, id: str, token: str, table: list, title: str) -> str:
        """Start posting a table to Discord (legacy API).

        Args:
            id: Discord channel ID
            token: Discord bot token
            table: List of table rows as strings
            title: Title for the table

        Returns:
            Empty string on success, error message on failure
        """
        return self._service.post_table(
            channel_id=id, token=token, table_data=table, title=title
        )
