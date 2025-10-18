# Lambda Modernization Templates

## Overview

This document provides before/after code examples for modernizing Lambda functions to use the repository and service patterns. Each template shows the transformation from legacy facade usage to modern architecture with proper dependency injection, error handling, and logging.

## Template 1: Simple Lambda Handler (Month Lambda)

### Before: Legacy Pattern
```python
import json
from irus import IrusResources, IrusReport, IrusMonth
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = IrusResources.logger()

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    status = 200
    headers = {"Content-Type": "application/json"}

    month = event["month"]
    body = {
        'template': '''# Report for Month {}''',
        'month': month,
        'invasions': '0',
        'active': '0',
        'members': '0',
        'participation': '0',
        'url': 'TBD'
    }

    try:
        # Direct usage of legacy classes
        report = IrusMonth.from_invasion_stats(month=int(month[4:6]), year=int(month[:4]))
        body['invasions'] = report.invasions
        body['active'] = report.active
        body['members'] = len(report.report)
        body['participation'] = report.participation

        export = IrusReport.from_month(report, gold=0)
        body['url'] = export.msg

    except Exception as e:
        status = 500
        body['url'] = f'Error generating report for {month}: {e}'

    return {
        "statusCode": status,
        "headers": headers,
        "body": body
    }
```

### After: Modern Pattern
```python
import json
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus.container import IrusContainer
from irus.services.report_generation import ReportGenerationService

@IrusContainer.create_production().logger().inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    """Modern Lambda handler using dependency injection and service layer."""

    # Initialize container and services
    container = IrusContainer.create_production()
    logger = container.logger()
    report_service = ReportGenerationService(container)

    try:
        # Extract and validate input
        month_str = event.get("month")
        if not month_str or len(month_str) != 6:
            raise ValueError(f"Invalid month format: {month_str}")

        month = int(month_str[4:6])
        year = int(month_str[:4])

        # Use service layer for business logic
        report_data = report_service.generate_monthly_report(year, month)

        # Format response
        response_body = {
            'template': '''# Report for Month {}''',
            'month': month_str,
            'invasions': report_data['invasions'],
            'active': report_data['active_members'],
            'members': report_data['total_members'],
            'participation': report_data['participation'],
            'url': report_data['report_url']
        }

        logger.info(f"Successfully generated monthly report for {month_str}")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": response_body
        }

    except ValueError as e:
        logger.warning(f"Validation error for monthly report: {e}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": {"error": f"Invalid input: {e}"}
        }

    except Exception as e:
        logger.error(f"Unexpected error generating monthly report: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": {"error": f"Internal server error: {e}"}
        }
```

## Template 2: Legacy Facade Replacement (Invasion Lambda)

### Before: Legacy Facade Usage
```python
import json
from irus import IrusResources, IrusLadder, IrusInvasion, IrusReport
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = IrusResources.logger()

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    name = event["invasion"]

    try:
        # Legacy facade usage
        invasion = IrusInvasion.from_table(name)
        ladder = IrusLadder.from_invasion(invasion)

        # Direct business logic in handler
        body = {
            'name': name,
            'ranks': ladder.count(),
            'members': ladder.members(),
            'memberlist': ladder.list(member=True),
            'nonmemberlist': ladder.list(member=False),
        }

        contiguous = ladder.contiguous_from_1_until()
        if contiguous != ladder.count():
            body['contiguous'] = f"*Ladder may be incomplete, starting from rank {contiguous}*"
        else:
            body['contiguous'] = 'Yes'

        report = IrusReport.from_invasion(ladder)
        body['url'] = report.msg

    except Exception as e:
        return {"statusCode": 500, "body": f'Error: {e}'}

    return {"statusCode": 200, "body": body}
```

### After: Modern Repository and Service Pattern
```python
import json
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus.container import IrusContainer
from irus.repositories.invasion import InvasionRepository
from irus.repositories.ladder import LadderRepository
from irus.services.report_generation import ReportGenerationService

@IrusContainer.create_production().logger().inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    """Modern Lambda handler for invasion report generation."""

    # Initialize container and dependencies
    container = IrusContainer.create_production()
    logger = container.logger()
    invasion_repo = InvasionRepository(container)
    ladder_repo = LadderRepository(container)
    report_service = ReportGenerationService(container)

    try:
        # Extract and validate input
        invasion_name = event.get("invasion")
        if not invasion_name:
            raise ValueError("Missing invasion name in request")

        logger.info(f"Generating invasion report for {invasion_name}")

        # Use repositories for data access
        invasion = invasion_repo.get_by_name(invasion_name)
        if not invasion:
            raise ValueError(f"Invasion {invasion_name} not found")

        ladder = ladder_repo.get_ladder(invasion_name)
        if not ladder:
            raise ValueError(f"No ladder data found for invasion {invasion_name}")

        # Use service layer for business logic
        report_data = report_service.generate_invasion_report(invasion_name)

        # Format response with proper structure
        response_body = {
            'template': '''# Report for Invasion {}''',
            'name': invasion_name,
            'ranks': report_data['total_ranks'],
            'members': report_data['member_count'],
            'memberlist': report_data['member_list'],
            'nonmemberlist': report_data['non_member_list'],
            'contiguous': report_data['contiguous_status'],
            'url': report_data['report_url']
        }

        logger.info(f"Successfully generated invasion report for {invasion_name}")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": response_body
        }

    except ValueError as e:
        logger.warning(f"Validation error for invasion report: {e}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": {"error": f"Invalid request: {e}"}
        }

    except Exception as e:
        logger.error(f"Unexpected error generating invasion report: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": {"error": f"Internal server error: {e}"}
        }
```

## Template 3: Complex File Processing (Process Lambda)

### Before: Direct AWS SDK and Legacy Facades
```python
import urllib3
import json
from irus import IrusResources, IrusMemberList, IrusLadder, IrusInvasion
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = IrusResources.logger()
s3 = IrusResources.s3()
bucket_name = IrusResources.bucket_name()
pool_mgr = urllib3.PoolManager()

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    name = event["invasion"]
    filename = event["filename"]
    url = event["url"]
    target = event["folder"] + filename
    process = event["process"]

    try:
        # Direct S3 operations
        if filename[-4:] != '.png':
            raise ValueError(f'File {filename} is not a PNG')

        s3.upload_fileobj(
            pool_mgr.request('GET', url, preload_content=False),
            bucket_name,
            target
        )

        # Legacy facade usage with business logic
        members = IrusMemberList()
        invasion = IrusInvasion.from_table(name)

        if process == 'Ladder':
            ladder = IrusLadder.from_ladder_image(invasion, members, bucket_name, target)
        elif process == 'Roster':
            ladder = IrusLadder.from_roster_image(invasion, members, bucket_name, target)
        else:
            raise ValueError(f'Unknown process {process}')

        data = f'Successful download of {filename}. ' + ladder.str()

    except Exception as e:
        return {"statusCode": 400, "body": f'Error: {e}'}

    return {"statusCode": 200, "body": data}
```

### After: Modern Service Layer Pattern
```python
import json
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus.container import IrusContainer
from irus.services.file_management import FileManagementService
from irus.services.ladder_extraction import LadderExtractionService
from irus.repositories.invasion import InvasionRepository
from irus.repositories.member import MemberRepository

@IrusContainer.create_production().logger().inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    """Modern Lambda handler for file processing and ladder extraction."""

    # Initialize container and services
    container = IrusContainer.create_production()
    logger = container.logger()
    file_service = FileManagementService(container)
    extraction_service = LadderExtractionService(container)
    invasion_repo = InvasionRepository(container)
    member_repo = MemberRepository(container)

    try:
        # Extract and validate input
        invasion_name = event.get("invasion")
        filename = event.get("filename")
        file_url = event.get("url")
        folder = event.get("folder", "")
        process_type = event.get("process")

        if not all([invasion_name, filename, file_url, process_type]):
            raise ValueError("Missing required parameters")

        if process_type not in ['Ladder', 'Roster']:
            raise ValueError(f"Invalid process type: {process_type}")

        logger.info(f"Processing {process_type} file {filename} for invasion {invasion_name}")

        # Validate file type using service
        if not file_service.validate_file_type(filename):
            raise ValueError(f"Invalid file type: {filename}")

        # Download file using service
        file_data = file_service.download_discord_file(file_url)

        # Upload to S3 using service
        s3_key = folder + filename
        s3_url = file_service.upload_to_s3(file_data, s3_key)

        # Get invasion and member data using repositories
        invasion = invasion_repo.get_by_name(invasion_name)
        if not invasion:
            raise ValueError(f"Invasion {invasion_name} not found")

        member_list = member_repo.get_active_members()

        # Extract ladder data using service
        if process_type == 'Ladder':
            ladder = extraction_service.extract_ladder_from_image(
                file_data, invasion_name
            )
        else:  # Roster
            ladder = extraction_service.extract_roster_from_image(
                file_data, invasion_name
            )

        # Validate extracted data
        is_valid = extraction_service.validate_extracted_data(ladder, member_list)
        if not is_valid:
            logger.warning(f"Validation issues found in extracted data for {filename}")

        response_data = {
            "message": f"Successfully processed {filename}",
            "invasion": invasion_name,
            "filename": filename,
            "s3_url": s3_url,
            "extracted_ranks": ladder.total_ranks if ladder else 0,
            "validation_passed": is_valid
        }

        logger.info(f"Successfully processed {process_type} file {filename} for invasion {invasion_name}")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response_data)
        }

    except ValueError as e:
        logger.warning(f"Validation error processing file: {e}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Invalid request: {e}"})
        }

    except Exception as e:
        logger.error(f"Unexpected error processing file: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Internal server error: {e}"})
        }
```

## Template 4: Complex Command Routing (Bot Lambda)

### Before: Monolithic Command Handler
```python
import json
import os
from datetime import datetime
import irus
from irus import (
    IrusInvasion, IrusMember, IrusLadder, IrusResources,
    IrusSecrets, IrusProcess, IrusPostTable
)

logger = IrusResources.logger()
app_id = IrusSecrets.app_id()
role_id = IrusSecrets.role_id()
process = IrusProcess()
post_table = IrusPostTable()

def invasion_add_cmd(options: list) -> IrusInvasion:
    # Complex command parsing logic
    now = datetime.now()
    day = now.day
    month = now.month
    year = now.year
    win = True

    for o in options:
        if o["name"] == "day":
            day = int(o["value"])
        elif o["name"] == "settlement":
            settlement = o["value"]
        # ... more parsing

    # Direct facade usage
    item = IrusInvasion.from_user(
        day=day, month=month, year=year,
        settlement=settlement, win=win, notes=notes
    )
    return item

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    # Signature verification, command parsing, and routing all mixed together
    verify_signature(event)
    body = json.loads(event["body"])

    if body["type"] == 2 and body["data"]["name"] == discord_cmd:
        subcommand = body["data"]["options"][0]
        name = subcommand["name"]

        if name == "invasion":
            content = invasion_cmd(app_id, body["token"], subcommand["options"][0], resolved)
        elif name == "member":
            content = member_cmd(subcommand["options"][0], resolved)
        # ... many more commands

    return {"statusCode": 200, "body": json.dumps(data)}
```

### After: Modern Service-Based Architecture
```python
import json
from aws_lambda_powertools.utilities.typing import LambdaContext
from irus.container import IrusContainer
from irus.services.discord_command import DiscordCommandService
from irus.services.invasion_workflow import InvasionWorkflowService
from irus.services.member_management import MemberManagementService
from irus.services.report_generation import ReportGenerationService

@IrusContainer.create_production().logger().inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    """Modern Lambda handler for Discord bot commands using service orchestration."""

    # Initialize container and services
    container = IrusContainer.create_production()
    logger = container.logger()
    command_service = DiscordCommandService(container)
    invasion_service = InvasionWorkflowService(container)
    member_service = MemberManagementService(container)
    report_service = ReportGenerationService(container)

    try:
        # Verify Discord signature using service
        command_service.verify_signature(event)

        # Parse Discord event using service
        command_request = command_service.parse_command(event)

        # Validate user permissions
        if not command_service.validate_permissions(
            command_request.user_id,
            command_request.command_name
        ):
            return command_service.format_error_response(
                "You do not have permission to run this command"
            )

        # Route command to appropriate service
        if command_request.command_name == "invasion":
            result = await handle_invasion_command(
                invasion_service, command_request
            )
        elif command_request.command_name == "member":
            result = await handle_member_command(
                member_service, command_request
            )
        elif command_request.command_name == "report":
            result = await handle_report_command(
                report_service, command_request
            )
        elif command_request.command_name in ["ladder", "ladders", "roster"]:
            result = await handle_file_processing_command(
                invasion_service, command_request
            )
        else:
            result = command_service.get_help_text(
                command_request.user_permissions
            )

        # Format response for Discord
        response = command_service.format_response(result)

        logger.info(f"Successfully processed Discord command: {command_request.command_name}")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(response)
        }

    except ValueError as e:
        logger.warning(f"Invalid Discord command: {e}")
        error_response = command_service.format_error_response(f"Invalid command: {e}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(error_response)
        }

    except Exception as e:
        logger.error(f"Unexpected error processing Discord command: {e}")
        error_response = command_service.format_error_response("Internal server error")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(error_response)
        }

async def handle_invasion_command(
    invasion_service: InvasionWorkflowService,
    command_request
) -> dict:
    """Handle invasion-related commands using workflow service."""

    if command_request.subcommand == "add":
        return invasion_service.create_invasion_workflow(command_request.parameters)
    elif command_request.subcommand == "edit":
        return invasion_service.edit_invasion_data(command_request.parameters)
    elif command_request.subcommand == "list":
        return invasion_service.list_invasions(command_request.parameters)
    else:
        raise ValueError(f"Unknown invasion subcommand: {command_request.subcommand}")

async def handle_member_command(
    member_service: MemberManagementService,
    command_request
) -> dict:
    """Handle member-related commands using member service."""

    if command_request.subcommand == "add":
        return member_service.add_member(command_request.parameters)
    elif command_request.subcommand == "remove":
        return member_service.remove_member(command_request.parameters)
    elif command_request.subcommand == "list":
        return member_service.list_members(command_request.parameters)
    else:
        raise ValueError(f"Unknown member subcommand: {command_request.subcommand}")

async def handle_report_command(
    report_service: ReportGenerationService,
    command_request
) -> dict:
    """Handle report generation commands using report service."""

    if command_request.subcommand == "invasion":
        return report_service.generate_invasion_report(command_request.parameters["invasion"])
    elif command_request.subcommand == "month":
        return report_service.generate_monthly_report(
            command_request.parameters.get("year"),
            command_request.parameters.get("month")
        )
    elif command_request.subcommand == "member":
        return report_service.generate_member_report(command_request.parameters["player"])
    else:
        raise ValueError(f"Unknown report subcommand: {command_request.subcommand}")
```

## Template 5: Missing Service Interface Designs

### ReportGenerationService Interface
```python
from typing import Dict, Any, Optional
from irus.container import IrusContainer
from irus.repositories.invasion import InvasionRepository
from irus.repositories.ladder import LadderRepository
from irus.repositories.member import MemberRepository

class ReportGenerationService:
    """Service for generating various types of reports with S3 storage."""

    def __init__(self, container: Optional[IrusContainer] = None):
        """Initialize service with dependency injection."""
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._invasion_repo = InvasionRepository(self._container)
        self._ladder_repo = LadderRepository(self._container)
        self._member_repo = MemberRepository(self._container)
        self._s3 = self._container.s3()
        self._bucket_name = self._container.bucket_name()

    def generate_invasion_report(self, invasion_name: str) -> Dict[str, Any]:
        """Generate comprehensive invasion report with statistics."""
        self._logger.info(f"Generating invasion report for {invasion_name}")

        invasion = self._invasion_repo.get_by_name(invasion_name)
        ladder = self._ladder_repo.get_ladder(invasion_name)

        # Calculate statistics
        total_ranks = ladder.total_ranks
        member_count = ladder.member_count
        contiguous_status = self._calculate_contiguous_status(ladder)

        # Generate CSV report and upload to S3
        csv_data = self._generate_invasion_csv(ladder)
        report_url = self._store_report_to_s3(csv_data, f"invasion-{invasion_name}")

        return {
            "invasion_name": invasion_name,
            "total_ranks": total_ranks,
            "member_count": member_count,
            "member_list": ladder.get_member_list(),
            "non_member_list": ladder.get_non_member_list(),
            "contiguous_status": contiguous_status,
            "report_url": report_url
        }

    def generate_monthly_report(self, year: int, month: int) -> Dict[str, Any]:
        """Generate monthly statistics report."""
        self._logger.info(f"Generating monthly report for {year}-{month:02d}")

        # Get monthly statistics
        invasions = self._invasion_repo.get_by_month(year, month)
        member_stats = self._calculate_monthly_member_stats(invasions)

        # Generate CSV report
        csv_data = self._generate_monthly_csv(member_stats)
        report_url = self._store_report_to_s3(csv_data, f"month-{year}{month:02d}")

        return {
            "year": year,
            "month": month,
            "invasions": len(invasions),
            "active_members": member_stats["active_count"],
            "total_members": member_stats["total_count"],
            "participation": member_stats["participation_sum"],
            "report_url": report_url
        }

    def generate_member_report(self, player: str) -> Dict[str, Any]:
        """Generate individual member performance report."""
        self._logger.info(f"Generating member report for {player}")

        member = self._member_repo.get_by_player(player)
        if not member:
            raise ValueError(f"Member {player} not found")

        # Calculate member statistics
        member_stats = self._calculate_member_stats(player)

        return {
            "player": player,
            "faction": member.faction,
            "start_date": member.start,
            "statistics": member_stats
        }

    def store_report_to_s3(self, report_data: str, report_type: str) -> str:
        """Store report data to S3 and return presigned URL."""
        key = f"reports/{report_type}-{int(time.time())}.csv"

        self._s3.put_object(
            Bucket=self._bucket_name,
            Key=key,
            Body=report_data,
            ContentType="text/csv"
        )

        # Generate presigned URL valid for 1 hour
        url = self._s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self._bucket_name, 'Key': key},
            ExpiresIn=3600
        )

        return url
```

### LadderExtractionService Interface
```python
from typing import Optional, Dict, Any
import boto3
from irus.container import IrusContainer
from irus.models.ladder import IrusLadder
from irus.models.member import IrusMemberList
from irus.services.image_processing import ImageProcessingService

class LadderExtractionService:
    """Service for OCR and ladder data extraction from invasion screenshots."""

    def __init__(self, container: Optional[IrusContainer] = None):
        """Initialize service with dependency injection."""
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._textract = self._container.textract()
        self._image_service = ImageProcessingService(self._container)

    def extract_ladder_from_image(
        self,
        image_data: bytes,
        invasion_name: str
    ) -> IrusLadder:
        """Extract ladder data from invasion screenshot using OCR."""
        self._logger.info(f"Extracting ladder data for invasion {invasion_name}")

        try:
            # Preprocess image for better OCR accuracy
            processed_image = self._image_service.preprocess_for_ocr(image_data)

            # Perform OCR using AWS Textract
            ocr_result = self._textract.analyze_document(
                Document={'Bytes': processed_image},
                FeatureTypes=['TABLES']
            )

            # Parse OCR results into ladder data
            ladder_data = self._parse_ladder_ocr_results(ocr_result)

            # Create and validate ladder object
            ladder = IrusLadder.from_extracted_data(invasion_name, ladder_data)

            self._logger.info(f"Successfully extracted {len(ladder_data)} ranks from ladder image")
            return ladder

        except Exception as e:
            self._logger.error(f"Failed to extract ladder data: {e}")
            raise ValueError(f"OCR extraction failed: {e}") from e

    def extract_roster_from_image(
        self,
        image_data: bytes,
        invasion_name: str
    ) -> IrusLadder:
        """Extract roster data from war board screenshot using OCR."""
        self._logger.info(f"Extracting roster data for invasion {invasion_name}")

        try:
            # Preprocess image specifically for roster format
            processed_image = self._image_service.preprocess_roster_image(image_data)

            # Perform OCR
            ocr_result = self._textract.analyze_document(
                Document={'Bytes': processed_image},
                FeatureTypes=['TABLES']
            )

            # Parse roster-specific OCR results
            roster_data = self._parse_roster_ocr_results(ocr_result)

            # Create ladder object from roster data
            ladder = IrusLadder.from_roster_data(invasion_name, roster_data)

            self._logger.info(f"Successfully extracted {len(roster_data)} members from roster image")
            return ladder

        except Exception as e:
            self._logger.error(f"Failed to extract roster data: {e}")
            raise ValueError(f"Roster OCR extraction failed: {e}") from e

    def validate_extracted_data(
        self,
        ladder: IrusLadder,
        member_list: IrusMemberList
    ) -> bool:
        """Validate extracted ladder data against known member list."""
        validation_issues = []

        # Check for known members not marked as members
        for rank_entry in ladder.ranks:
            if rank_entry.player in member_list.player_names:
                if not rank_entry.is_member:
                    validation_issues.append(
                        f"Known member {rank_entry.player} not marked as member at rank {rank_entry.rank}"
                    )

        # Check for suspicious player names (OCR errors)
        for rank_entry in ladder.ranks:
            if self._is_suspicious_player_name(rank_entry.player):
                validation_issues.append(
                    f"Suspicious player name at rank {rank_entry.rank}: {rank_entry.player}"
                )

        # Log validation issues
        if validation_issues:
            self._logger.warning(f"Validation issues found: {validation_issues}")
            return False

        return True

    def handle_extraction_errors(
        self,
        error: Exception,
        image_data: bytes
    ) -> Dict[str, Any]:
        """Handle OCR extraction errors with diagnostic information."""
        self._logger.error(f"OCR extraction error: {error}")

        # Analyze image for common issues
        image_analysis = self._image_service.analyze_image_quality(image_data)

        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "image_size": len(image_data),
            "image_quality": image_analysis,
            "suggested_fixes": self._get_suggested_fixes(image_analysis)
        }

        return error_info
```

### FileManagementService Interface
```python
import urllib3
from typing import Optional, Dict, Any
from irus.container import IrusContainer

class FileManagementService:
    """Service for Discord file downloads and S3 operations."""

    def __init__(self, container: Optional[IrusContainer] = None):
        """Initialize service with dependency injection."""
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._s3 = self._container.s3()
        self._bucket_name = self._container.bucket_name()
        self._pool_manager = urllib3.PoolManager()

    def download_discord_file(self, url: str) -> bytes:
        """Download file from Discord CDN with proper error handling."""
        self._logger.info(f"Downloading file from Discord: {url}")

        try:
            response = self._pool_manager.request(
                'GET',
                url,
                preload_content=False,
                timeout=30.0
            )

            if response.status != 200:
                raise ValueError(f"Failed to download file: HTTP {response.status}")

            file_data = response.read()

            # Validate file size
            if len(file_data) > 50 * 1024 * 1024:  # 50MB limit
                raise ValueError("File too large (>50MB)")

            self._logger.info(f"Successfully downloaded {len(file_data)} bytes")
            return file_data

        except Exception as e:
            self._logger.error(f"Failed to download Discord file: {e}")
            raise ValueError(f"Download failed: {e}") from e

    def upload_to_s3(self, file_data: bytes, key: str) -> str:
        """Upload file data to S3 with retry mechanism."""
        self._logger.info(f"Uploading {len(file_data)} bytes to S3: {key}")

        try:
            self._s3.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=file_data,
                ContentType=self._get_content_type(key)
            )

            s3_url = f"s3://{self._bucket_name}/{key}"
            self._logger.info(f"Successfully uploaded to S3: {s3_url}")
            return s3_url

        except Exception as e:
            self._logger.error(f"Failed to upload to S3: {e}")
            raise ValueError(f"S3 upload failed: {e}") from e

    def validate_file_type(self, filename: str) -> bool:
        """Validate file type and security constraints."""
        allowed_extensions = {'.png', '.jpg', '.jpeg'}

        # Check file extension
        file_ext = filename.lower()[-4:]
        if file_ext not in allowed_extensions:
            self._logger.warning(f"Invalid file extension: {file_ext}")
            return False

        return True

    def handle_download_errors(self, url: str, error: Exception) -> Dict[str, Any]:
        """Handle download errors with diagnostic information."""
        self._logger.error(f"Download error for {url}: {error}")

        error_info = {
            "url": url,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "retry_recommended": self._should_retry_download(error),
            "suggested_action": self._get_download_suggestion(error)
        }

        return error_info
```

## Error Handling and Logging Patterns

### Modern Error Handling Template
```python
from irus.container import IrusContainer
from irus.exceptions import ValidationError, RepositoryError, ServiceError

class ModernLambdaHandler:
    """Template for modern Lambda error handling patterns."""

    def __init__(self):
        self.container = IrusContainer.create_production()
        self.logger = self.container.logger()

    def handle_request(self, event: dict) -> dict:
        """Template method showing proper error handling hierarchy."""

        try:
            # Input validation
            self._validate_input(event)

            # Business logic
            result = self._process_request(event)

            # Success response
            return self._format_success_response(result)

        except ValidationError as e:
            # Client errors (400)
            self.logger.warning(f"Validation error: {e}")
            return self._format_error_response(400, f"Invalid input: {e}")

        except RepositoryError as e:
            # Data access errors (500)
            self.logger.error(f"Repository error: {e}")
            return self._format_error_response(500, "Data access error")

        except ServiceError as e:
            # Business logic errors (500)
            self.logger.error(f"Service error: {e}")
            return self._format_error_response(500, "Service error")

        except Exception as e:
            # Unexpected errors (500)
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            return self._format_error_response(500, "Internal server error")

    def _validate_input(self, event: dict) -> None:
        """Validate input and raise ValidationError for invalid data."""
        if not event:
            raise ValidationError("Empty event")

        # Add specific validation logic

    def _format_error_response(self, status_code: int, message: str) -> dict:
        """Format consistent error responses."""
        return {
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": message,
                "timestamp": datetime.utcnow().isoformat()
            })
        }
```

### Container Integration Pattern
```python
from irus.container import IrusContainer

# Production Lambda
def lambda_handler(event: dict, context: LambdaContext):
    container = IrusContainer.create_production()
    service = SomeService(container)
    return service.handle_request(event)

# Unit Test
def test_lambda_handler():
    container = IrusContainer.create_unit()
    service = SomeService(container)

    # Mock dependencies
    container.table().put_item.return_value = {}

    result = service.handle_request(test_event)
    assert result["statusCode"] == 200

# Integration Test
def test_lambda_integration(integration_container):
    service = SomeService(integration_container)
    result = service.handle_request(test_event)
    assert result["statusCode"] == 200
```

## Modernization Checklist

### For Each Lambda Function:
- [ ] Replace `IrusResources` with `IrusContainer.create_production()`
- [ ] Replace legacy facades with modern repositories and services
- [ ] Add proper input validation with clear error messages
- [ ] Implement structured error handling with appropriate HTTP status codes
- [ ] Add comprehensive logging with context information
- [ ] Create unit tests with mocked dependencies
- [ ] Create integration tests with real AWS resources

### Service Development Requirements:
- [ ] Design service interface and contracts
- [ ] Implement core business logic methods
- [ ] Add comprehensive error handling
- [ ] Create unit tests with >90% coverage
- [ ] Create integration tests with real AWS resources
- [ ] Document service usage patterns and examples
