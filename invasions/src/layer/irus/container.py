"""Dependency injection container for Irus resources.

This module provides a clean dependency injection container that can be easily
configured for both production and testing environments.
"""

import os
from contextlib import contextmanager
from typing import Any, Optional, Protocol


class TableProtocol(Protocol):
    """Protocol for DynamoDB table interface."""

    def get_item(self, **kwargs) -> dict[str, Any]: ...
    def put_item(self, **kwargs) -> dict[str, Any]: ...
    def delete_item(self, **kwargs) -> dict[str, Any]: ...
    def query(self, **kwargs) -> dict[str, Any]: ...
    def scan(self, **kwargs) -> dict[str, Any]: ...
    def update_item(self, **kwargs) -> dict[str, Any]: ...


class LoggerProtocol(Protocol):
    """Protocol for logger interface."""

    def info(self, message: str, **kwargs) -> None: ...
    def debug(self, message: str, **kwargs) -> None: ...
    def warning(self, message: str, **kwargs) -> None: ...
    def error(self, message: str, **kwargs) -> None: ...


class S3Protocol(Protocol):
    """Protocol for S3 client interface."""

    def get_object(self, **kwargs) -> dict[str, Any]: ...
    def put_object(self, **kwargs) -> dict[str, Any]: ...
    def delete_object(self, **kwargs) -> dict[str, Any]: ...
    def list_objects_v2(self, **kwargs) -> dict[str, Any]: ...


class TextractProtocol(Protocol):
    """Protocol for Textract client interface."""

    def detect_document_text(self, **kwargs) -> dict[str, Any]: ...
    def analyze_document(self, **kwargs) -> dict[str, Any]: ...


class IrusContainer:
    """Dependency injection container for Irus resources.

    This container manages AWS resources and provides dependency injection
    support for both production and testing environments.

    Example:
        # Production usage
        container = IrusContainer.create_production()
        table = container.table()

        # Test usage
        mock_table = Mock()
        container = IrusContainer.create_test(table=mock_table)
        table = container.table()

        # Context manager for tests
        with IrusContainer.test_context(table=mock_table):
            # Code that uses IrusContainer.default() will get test dependencies
            repo = MemberRepository()
    """

    _default_instance: Optional["IrusContainer"] = None

    def __init__(
        self,
        table: TableProtocol | None = None,
        logger: LoggerProtocol | None = None,
        s3: S3Protocol | None = None,
        s3_resource: Any | None = None,
        textract: TextractProtocol | None = None,
        bucket_name: str | None = None,
        table_name: str | None = None,
        webhook_url: str | None = None,
        process_step_function_arn: str | None = None,
        post_step_function_arn: str | None = None,
        image_contrast_factor: float | None = None,
        image_saturation_factor: float | None = None,
    ):
        """Initialize container with optional dependencies."""
        self._table = table
        self._logger = logger
        self._s3 = s3
        self._s3_resource = s3_resource
        self._textract = textract
        self._bucket_name = bucket_name
        self._table_name = table_name
        self._webhook_url = webhook_url
        self._process_step_function_arn = process_step_function_arn
        self._post_step_function_arn = post_step_function_arn
        self._image_contrast_factor = image_contrast_factor
        self._image_saturation_factor = image_saturation_factor

        # Lazy-loaded AWS resources
        self._session = None
        self._dynamodb = None
        self._state_machine = None

    @classmethod
    def create_production(cls) -> "IrusContainer":
        """Create container for production environment.

        This will use real AWS resources and environment variables.
        """
        return cls()

    @classmethod
    def create_test(
        cls,
        table: TableProtocol | None = None,
        logger: LoggerProtocol | None = None,
        s3: S3Protocol | None = None,
        **kwargs,
    ) -> "IrusContainer":
        """Create container for testing with mocked dependencies.

        Args:
            table: Mock DynamoDB table
            logger: Mock logger
            s3: Mock S3 client
            **kwargs: Other optional dependencies

        Returns:
            Container configured for testing
        """
        from unittest.mock import Mock

        return cls(
            table=table or Mock(spec=TableProtocol),
            logger=logger or Mock(spec=LoggerProtocol),
            s3=s3 or Mock(spec=S3Protocol),
            bucket_name="test-bucket",
            table_name="test-table",
            webhook_url="https://test.webhook.com",
            process_step_function_arn="arn:aws:states:test",
            post_step_function_arn="arn:aws:states:test",
            image_contrast_factor=1.5,
            image_saturation_factor=0.7,
            **kwargs,
        )

    @classmethod
    def create_unit(cls, **kwargs) -> "IrusContainer":
        """Create container for unit testing with fully mocked dependencies.

        This is an alias for create_test() for consistency with style guide.

        Returns:
            Container configured for unit testing
        """
        return cls.create_test(**kwargs)

    @classmethod
    def set_default(cls, container: "IrusContainer") -> None:
        """Set the default container instance."""
        cls._default_instance = container

    @classmethod
    def create_integration(
        cls, aws_resources: dict[str, str], stack_name: str
    ) -> "IrusContainer":
        """Create container for integration testing with SAM-discovered resources.

        This method sets environment variables from SAM-discovered resources
        and includes safety checks to ensure we're using expected environment.

        Args:
            aws_resources: Dictionary of AWS resources from SAM discovery
            stack_name: Expected stack name prefix for safety checks (from config)

        Returns:
            Container configured for integration testing with real AWS clients

        Raises:
            ValueError: If resources don't appear to be from expected environment
        """
        import os

        # Safety checks - ensure we're using the expected environment resources
        table_name = aws_resources.get("table_name", "")
        bucket_name = aws_resources.get("bucket_name", "")
        expected_prefix = stack_name.lower()

        if not table_name or expected_prefix not in table_name.lower():
            raise ValueError(
                f"Not using expected environment - table: {table_name}, expected prefix: {expected_prefix}"
            )

        if not bucket_name or expected_prefix not in bucket_name.lower():
            raise ValueError(
                f"Not using expected environment - bucket: {bucket_name}, expected prefix: {expected_prefix}"
            )

        # Set environment variables from discovered resources
        os.environ["TABLE_NAME"] = table_name
        os.environ["BUCKET_NAME"] = bucket_name
        os.environ["WEBHOOK_URL"] = aws_resources.get(
            "webhook_url", "https://test.webhook.com"
        )

        if process_arn := aws_resources.get("process_step_function_arn"):
            os.environ["PROCESS_STEP_FUNCTION_ARN"] = process_arn

        if post_arn := aws_resources.get("post_step_function_arn"):
            os.environ["POST_STEP_FUNCTION_ARN"] = post_arn

        # Create production container which will use the env vars we just set
        return cls.create_production()

    @classmethod
    def default(cls) -> "IrusContainer":
        """Get the default container instance.

        If no default is set, creates a production container.
        """
        if cls._default_instance is None:
            cls._default_instance = cls.create_production()
        return cls._default_instance

    @classmethod
    @contextmanager
    def test_context(cls, **kwargs):
        """Context manager for testing with temporary container.

        Example:
            with IrusContainer.test_context(table=mock_table):
                # Code here will use the test container
                repo = MemberRepository()
        """
        old_default = cls._default_instance
        test_container = cls.create_test(**kwargs)
        cls.set_default(test_container)
        try:
            yield test_container
        finally:
            cls._default_instance = old_default

    def table(self) -> TableProtocol:
        """Get DynamoDB table."""
        if self._table is not None:
            return self._table

        # Create real table for production
        if self._dynamodb is None:
            self._dynamodb = self._get_session().resource("dynamodb")

        table_name = self.table_name()
        self._table = self._dynamodb.Table(table_name)
        return self._table

    def logger(self) -> LoggerProtocol:
        """Get logger."""
        if self._logger is not None:
            return self._logger

        # Create real logger for production
        from aws_lambda_powertools import Logger

        self._logger = Logger()
        return self._logger

    def s3(self) -> S3Protocol:
        """Get S3 client."""
        if self._s3 is not None:
            return self._s3

        # Create real S3 client for production
        self._s3 = self._get_session().client("s3")
        return self._s3

    def s3_resource(self) -> Any:
        """Get S3 resource."""
        if self._s3_resource is not None:
            return self._s3_resource

        # Create real S3 resource for production
        self._s3_resource = self._get_session().resource("s3")
        return self._s3_resource

    def textract(self) -> TextractProtocol:
        """Get Textract client."""
        if self._textract is not None:
            return self._textract

        # Create real Textract client for production
        self._textract = self._get_session().client("textract")
        return self._textract

    def state_machine(self) -> Any:
        """Get Step Functions client."""
        if self._state_machine is not None:
            return self._state_machine

        # Create real Step Functions client for production
        self._state_machine = self._get_session().client("stepfunctions")
        return self._state_machine

    def bucket_name(self) -> str:
        """Get S3 bucket name."""
        if self._bucket_name is not None:
            return self._bucket_name

        bucket_name = os.environ.get("BUCKET_NAME")
        if bucket_name is None:
            raise ValueError("BUCKET_NAME environment variable is not set")

        self._bucket_name = bucket_name
        return self._bucket_name

    def table_name(self) -> str:
        """Get DynamoDB table name."""
        if self._table_name is not None:
            return self._table_name

        table_name = os.environ.get("TABLE_NAME")
        if table_name is None:
            raise ValueError("TABLE_NAME environment variable is not set")

        self._table_name = table_name
        return self._table_name

    def webhook_url(self) -> str:
        """Get Discord webhook URL."""
        if self._webhook_url is not None:
            return self._webhook_url

        webhook_url = os.environ.get("WEBHOOK_URL")
        if webhook_url is None:
            raise ValueError("WEBHOOK_URL environment variable is not set")

        self._webhook_url = webhook_url
        return self._webhook_url

    def process_step_function_arn(self) -> str:
        """Get process step function ARN."""
        if self._process_step_function_arn is not None:
            return self._process_step_function_arn

        arn = os.environ.get("PROCESS_STEP_FUNC")
        if arn is None:
            raise ValueError("PROCESS_STEP_FUNC environment variable is not set")

        self._process_step_function_arn = arn
        return self._process_step_function_arn

    def post_step_function_arn(self) -> str:
        """Get post step function ARN."""
        if self._post_step_function_arn is not None:
            return self._post_step_function_arn

        arn = os.environ.get("POST_STEP_FUNC")
        if arn is None:
            raise ValueError("POST_STEP_FUNC environment variable is not set")

        self._post_step_function_arn = arn
        return self._post_step_function_arn

    def image_contrast_factor(self) -> float:
        """Get image contrast factor."""
        if self._image_contrast_factor is not None:
            return self._image_contrast_factor

        self._image_contrast_factor = float(
            os.environ.get("IMAGE_CONTRAST_FACTOR", "1.5")
        )
        return self._image_contrast_factor

    def image_saturation_factor(self) -> float:
        """Get image saturation factor."""
        if self._image_saturation_factor is not None:
            return self._image_saturation_factor

        self._image_saturation_factor = float(
            os.environ.get("IMAGE_SATURATION_FACTOR", "0.7")
        )
        return self._image_saturation_factor

    def _get_session(self):
        """Get or create boto3 session."""
        if self._session is None:
            import boto3

            self._session = boto3.session.Session()
        return self._session

    def reset(self) -> None:
        """Reset all cached resources (useful for testing)."""
        self._table = None
        self._logger = None
        self._s3 = None
        self._s3_resource = None
        self._textract = None
        self._state_machine = None
        self._session = None
        self._dynamodb = None
