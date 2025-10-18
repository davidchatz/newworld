"""Discord event fixtures for Lambda testing."""

import json
import time
from uuid import uuid4

import pytest

from tests.integration.conftest import get_test_date_components


@pytest.fixture
def discord_ping_event():
    """Discord ping event (type 1)."""
    return {
        "body": json.dumps({"type": 1}),
        "headers": {
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": str(int(time.time())),
        },
    }


@pytest.fixture
def discord_command_base():
    """Base Discord slash command event."""
    return {
        "body": json.dumps(
            {
                "type": 2,
                "data": {"name": "irus", "options": []},
                "member": {"roles": ["admin_role_id"]},
                "token": f"test_token_{uuid4().hex[:8]}",
            }
        ),
        "headers": {
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": str(int(time.time())),
        },
    }


@pytest.fixture
def discord_help_command(discord_command_base):
    """Discord help command event."""
    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [{"name": "help"}]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_member_add_command(discord_command_base):
    """Discord member add command with test data."""
    timestamp = int(time.time())
    unique_id = uuid4().hex[:8]
    date_components = get_test_date_components()

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "member",
            "options": [
                {
                    "name": "add",
                    "options": [
                        {
                            "name": "player",
                            "value": f"TestPlayer-{timestamp}-{unique_id}",
                        },
                        {"name": "faction", "value": "yellow"},
                        {"name": "day", "value": date_components["day"]},
                        {"name": "month", "value": date_components["month"]},
                        {"name": "year", "value": date_components["year"]},
                    ],
                }
            ],
        }
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_member_remove_command(discord_command_base):
    """Discord member remove command with test data."""
    timestamp = int(time.time())
    unique_id = uuid4().hex[:8]

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "member",
            "options": [
                {
                    "name": "remove",
                    "options": [
                        {
                            "name": "player",
                            "value": f"TestPlayer-{timestamp}-{unique_id}",
                        }
                    ],
                }
            ],
        }
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_invasion_add_command(discord_command_base):
    """Discord invasion add command with test data."""
    date_components = get_test_date_components()

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "invasion",
            "options": [
                {
                    "name": "add",
                    "options": [
                        {"name": "settlement", "value": "ef"},
                        {"name": "win", "value": True},
                        {"name": "day", "value": date_components["day"]},
                        {"name": "month", "value": date_components["month"]},
                        {"name": "year", "value": date_components["year"]},
                        {"name": "notes", "value": "Test invasion"},
                    ],
                }
            ],
        }
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_invasion_list_command(discord_command_base):
    """Discord invasion list command with test data."""
    date_components = get_test_date_components()

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "invasion",
            "options": [
                {
                    "name": "list",
                    "options": [
                        {"name": "month", "value": date_components["month"]},
                        {"name": "year", "value": date_components["year"]},
                    ],
                }
            ],
        }
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_ladder_command(discord_command_base):
    """Discord ladder upload command with test data."""
    date_components = get_test_date_components()

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "ladder",
            "options": [
                {"name": "settlement", "value": "ef"},
                {"name": "win", "value": True},
                {"name": "file1", "value": "attachment_id_123"},
                {"name": "day", "value": date_components["day"]},
                {"name": "month", "value": date_components["month"]},
                {"name": "year", "value": date_components["year"]},
            ],
        }
    ]
    body["data"]["resolved"] = {
        "attachments": {
            "attachment_id_123": {
                "filename": "ladder.png",
                "url": "https://cdn.discordapp.com/attachments/123/456/ladder.png",
            }
        }
    }
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_ladders_command(discord_command_base):
    """Discord ladders (multiple files) upload command with test data."""
    date_components = get_test_date_components()

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "ladders",
            "options": [
                {"name": "settlement", "value": "bw"},
                {"name": "win", "value": False},
                {"name": "file1", "value": "attachment_1"},
                {"name": "file2", "value": "attachment_2"},
                {"name": "file3", "value": "attachment_3"},
                {"name": "file4", "value": "attachment_4"},
                {"name": "file5", "value": "attachment_5"},
                {"name": "file6", "value": "attachment_6"},
                {"name": "file7", "value": "attachment_7"},
                {"name": "day", "value": date_components["day"]},
                {"name": "month", "value": date_components["month"]},
                {"name": "year", "value": date_components["year"]},
            ],
        }
    ]
    body["data"]["resolved"] = {
        "attachments": {
            f"attachment_{i}": {
                "filename": f"ladder_{i}.png",
                "url": f"https://cdn.discordapp.com/attachments/123/456/ladder_{i}.png",
            }
            for i in range(1, 8)
        }
    }
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_roster_command(discord_command_base):
    """Discord roster upload command with test data."""
    date_components = get_test_date_components()

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "roster",
            "options": [
                {"name": "settlement", "value": "ww"},
                {"name": "win", "value": True},
                {"name": "file1", "value": "roster_attachment"},
                {"name": "day", "value": date_components["day"]},
                {"name": "month", "value": date_components["month"]},
                {"name": "year", "value": date_components["year"]},
            ],
        }
    ]
    body["data"]["resolved"] = {
        "attachments": {
            "roster_attachment": {
                "filename": "roster.png",
                "url": "https://cdn.discordapp.com/attachments/123/456/roster.png",
            }
        }
    }
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_report_invasion_command(discord_command_base):
    """Discord invasion report command with test data."""
    date_components = get_test_date_components()
    invasion_name = f"{date_components['date_string']}-ef"

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "report",
            "options": [
                {
                    "name": "invasion",
                    "options": [{"name": "invasion", "value": invasion_name}],
                }
            ],
        }
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_report_month_command(discord_command_base):
    """Discord monthly report command with test data."""
    date_components = get_test_date_components()

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "report",
            "options": [
                {
                    "name": "month",
                    "options": [
                        {"name": "month", "value": date_components["month"]},
                        {"name": "year", "value": date_components["year"]},
                    ],
                }
            ],
        }
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_report_member_command(discord_command_base):
    """Discord member report command with test data."""
    timestamp = int(time.time())
    unique_id = uuid4().hex[:8]
    date_components = get_test_date_components()

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "report",
            "options": [
                {
                    "name": "member",
                    "options": [
                        {
                            "name": "player",
                            "value": f"TestPlayer-{timestamp}-{unique_id}",
                        },
                        {"name": "month", "value": date_components["month"]},
                        {"name": "year", "value": date_components["year"]},
                    ],
                }
            ],
        }
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_display_invasion_command(discord_command_base):
    """Discord display invasion command with test data."""
    date_components = get_test_date_components()
    invasion_name = f"{date_components['date_string']}-ef"

    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {
            "name": "display",
            "options": [
                {
                    "name": "invasion",
                    "options": [{"name": "invasion", "value": invasion_name}],
                }
            ],
        }
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_display_members_command(discord_command_base):
    """Discord display members command."""
    body = json.loads(discord_command_base["body"])
    body["data"]["options"] = [
        {"name": "display", "options": [{"name": "members", "options": []}]}
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_unauthorized_user(discord_command_base):
    """Discord command from unauthorized user."""
    body = json.loads(discord_command_base["body"])
    body["member"]["roles"] = ["regular_user_role"]  # Remove admin role
    body["data"]["options"] = [
        {"name": "member", "options": [{"name": "add", "options": []}]}
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_regular_user_command(discord_command_base):
    """Discord command from regular user (non-admin)."""
    body = json.loads(discord_command_base["body"])
    body["member"]["roles"] = ["regular_user_role"]
    body["data"]["options"] = [
        {"name": "report", "options": [{"name": "month", "options": []}]}
    ]
    discord_command_base["body"] = json.dumps(body)
    return discord_command_base


@pytest.fixture
def discord_invalid_signature_event(discord_command_base):
    """Discord event with invalid signature."""
    discord_command_base["headers"]["x-signature-ed25519"] = "invalid_signature_hex"
    return discord_command_base


@pytest.fixture
def discord_missing_headers_event(discord_command_base):
    """Discord event with missing required headers."""
    del discord_command_base["headers"]["x-signature-ed25519"]
    return discord_command_base


# Lambda event fixtures for other Lambda functions


@pytest.fixture
def process_lambda_event():
    """Process Lambda event fixture."""
    date_components = get_test_date_components()
    invasion_name = f"{date_components['date_string']}-ef"

    return {
        "invasion": invasion_name,
        "filename": "test_ladder.png",
        "url": "https://cdn.discordapp.com/attachments/123/456/test_ladder.png",
        "folder": f"invasions/{invasion_name}/",
        "process": "Ladder",
    }


@pytest.fixture
def invasion_lambda_event():
    """Invasion Lambda event fixture."""
    date_components = get_test_date_components()
    invasion_name = f"{date_components['date_string']}-ef"

    return {"invasion": invasion_name}


@pytest.fixture
def month_lambda_event():
    """Month Lambda event fixture."""
    date_components = get_test_date_components()
    month_string = f"{date_components['year']}{date_components['month']:02d}"

    return {"month": month_string}


# Utility functions for creating custom events


def create_discord_command_event(
    command_name, subcommand_name, options=None, admin=True, resolved=None
):
    """Create a custom Discord command event.

    Args:
        command_name: Top-level command name (e.g., "member", "invasion")
        subcommand_name: Subcommand name (e.g., "add", "list")
        options: List of command options
        admin: Whether user has admin role
        resolved: Resolved attachments or other data

    Returns:
        Discord event dictionary
    """
    options = options or []
    roles = ["admin_role_id"] if admin else ["regular_user_role"]

    event = {
        "body": json.dumps(
            {
                "type": 2,
                "data": {
                    "name": "irus",
                    "options": [
                        {
                            "name": command_name,
                            "options": [{"name": subcommand_name, "options": options}],
                        }
                    ],
                },
                "member": {"roles": roles},
                "token": f"test_token_{uuid4().hex[:8]}",
            }
        ),
        "headers": {
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": str(int(time.time())),
        },
    }

    if resolved:
        body = json.loads(event["body"])
        body["data"]["resolved"] = resolved
        event["body"] = json.dumps(body)

    return event


def create_process_event(invasion_name, filename, url, process_type="Ladder"):
    """Create a Process Lambda event.

    Args:
        invasion_name: Name of the invasion (e.g., "99151228-ef")
        filename: Name of the file being processed
        url: URL to download the file from
        process_type: Type of processing ("Ladder" or "Roster")

    Returns:
        Process Lambda event dictionary
    """
    return {
        "invasion": invasion_name,
        "filename": filename,
        "url": url,
        "folder": f"invasions/{invasion_name}/",
        "process": process_type,
    }
