"""Tests for process service classes."""

import json
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from irus.container import IrusContainer
from irus.models.invasion import IrusInvasion
from irus.process import IrusFiles, IrusProcess


class TestIrusFiles:
    """Test suite for IrusFiles class."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        return IrusContainer.create_test()

    @pytest.fixture
    def files(self, container):
        """Create IrusFiles instance with test container."""
        return IrusFiles(container)

    def test_init(self, container):
        """Test IrusFiles initialization."""
        files = IrusFiles(container)

        assert files.files == []
        assert files._container is container
        assert files._logger is not None

    def test_init_default_container(self):
        """Test IrusFiles initialization with default container."""
        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock(spec=IrusContainer)
            mock_container.logger.return_value = Mock()
            mock_default.return_value = mock_container

            files = IrusFiles()

            assert files._container is mock_container
            mock_default.assert_called_once()

    def test_append(self, files):
        """Test appending files to collection."""
        files.append("test_name", "test_attachment")

        assert len(files.files) == 1
        assert files.files[0] == {"name": "test_name", "attachment": "test_attachment"}

    def test_append_multiple(self, files):
        """Test appending multiple files."""
        files.append("file1", "attach1")
        files.append("file2", "attach2")

        assert len(files.files) == 2
        assert files.files[0]["name"] == "file1"
        assert files.files[1]["name"] == "file2"

    def test_update_success(self, files):
        """Test updating files with attachment metadata."""
        files.append("test_name", "test_attachment")

        attachments = {
            "test_attachment": {
                "filename": "test_file.png",
                "url": "https://example.com/test_file.png",
            }
        }

        files.update(attachments)

        assert files.files[0]["filename"] == "test_file.png"
        assert files.files[0]["url"] == "https://example.com/test_file.png"

    def test_update_missing_filename(self, files):
        """Test update raises error when filename is missing."""
        files.append("test_name", "test_attachment")

        attachments = {
            "other_attachment": {
                "filename": "other_file.png",
                "url": "https://example.com/other_file.png",
            }
        }

        # First expect KeyError for missing attachment
        with pytest.raises(KeyError):
            files.update(attachments)

    def test_get(self, files):
        """Test getting file list."""
        files.append("test_name", "test_attachment")

        result = files.get()

        assert result == files.files
        assert len(result) == 1

    def test_str(self, files):
        """Test string representation."""
        assert files.str() == "0 files"

        files.append("file1", "attach1")
        assert files.str() == "1 files"

        files.append("file2", "attach2")
        assert files.str() == "2 files"


class TestIrusProcess:
    """Test suite for IrusProcess class."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        mock_container = IrusContainer.create_test()
        # Create proper mock for step machine
        mock_step_machine = Mock()
        mock_container.state_machine = Mock(return_value=mock_step_machine)
        mock_container.webhook_url = Mock(return_value="https://test.webhook.com")
        mock_container.process_step_function_arn = Mock(
            return_value="arn:aws:states:test"
        )
        return mock_container

    @pytest.fixture
    def process(self, container):
        """Create IrusProcess instance with test container."""
        return IrusProcess(container)

    @pytest.fixture
    def sample_invasion(self):
        """Create sample invasion for testing."""
        return IrusInvasion(
            name="20240301-bw",
            settlement="bw",
            win=True,
            date=20240301,
            year=2024,
            month=3,
            day=1,
        )

    @pytest.fixture
    def sample_files(self, container):
        """Create sample files for testing."""
        files = IrusFiles(container)
        files.append("screenshot1", "attach1")
        files.append("screenshot2", "attach2")
        return files

    def test_init(self, container):
        """Test IrusProcess initialization."""
        process = IrusProcess(container)

        assert process._container is container
        assert process._logger is not None
        assert process._step_machine is not None
        assert process.step_func_arn == "arn:aws:states:test"
        assert process.webhook_url == "https://test.webhook.com"

    def test_init_default_container(self):
        """Test IrusProcess initialization with default container."""
        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock(spec=IrusContainer)
            mock_container.logger.return_value = Mock()
            mock_container.state_machine.return_value = Mock()
            mock_container.process_step_function_arn.return_value = "test_arn"
            mock_container.webhook_url.return_value = "test_url"
            mock_default.return_value = mock_container

            process = IrusProcess()

            assert process._container is mock_container
            mock_default.assert_called_once()

    def test_start_ladder_success(self, process, sample_invasion, sample_files):
        """Test starting ladder processing workflow successfully."""
        # Mock the files have been updated with attachment metadata
        sample_files.files[0].update(
            {"filename": "screen1.png", "url": "https://example.com/screen1.png"}
        )
        sample_files.files[1].update(
            {"filename": "screen2.png", "url": "https://example.com/screen2.png"}
        )

        result = process.start(
            "test_id", "test_token", sample_invasion, sample_files, "Ladder"
        )

        # Verify step function was called with correct parameters
        process._step_machine.start_execution.assert_called_once()
        call_args = process._step_machine.start_execution.call_args

        assert call_args[1]["stateMachineArn"] == "arn:aws:states:test"

        # Parse the input JSON
        input_data = json.loads(call_args[1]["input"])
        assert input_data["post"] == "https://test.webhook.com/test_id/test_token"
        assert input_data["invasion"] == "20240301-bw"
        assert input_data["folder"] == "ladders/20240301-bw/"
        assert input_data["process"] == "Ladder"
        assert input_data["month"] == "202403"
        assert len(input_data["files"]) == 2

        assert result == "In Progress: Downloading and processing screenshot(s)"

    def test_start_roster_success(self, process, sample_invasion, sample_files):
        """Test starting roster processing workflow successfully."""
        process.start("test_id", "test_token", sample_invasion, sample_files, "Roster")

        # Verify step function was called
        process._step_machine.start_execution.assert_called_once()
        call_args = process._step_machine.start_execution.call_args

        # Parse the input JSON
        input_data = json.loads(call_args[1]["input"])
        assert input_data["folder"] == "roster/20240301-bw/"
        assert input_data["process"] == "Roster"

    def test_start_unknown_process_type(self, process, sample_invasion, sample_files):
        """Test starting workflow with unknown process type raises error."""
        with pytest.raises(
            ValueError, match="invasion_screenshots: Unknown process InvalidType"
        ):
            process.start(
                "test_id", "test_token", sample_invasion, sample_files, "InvalidType"
            )

    def test_start_step_function_error(self, process, sample_invasion, sample_files):
        """Test handling step function execution errors."""
        # Mock step function to raise ClientError
        error = ClientError(
            error_response={
                "Error": {"Code": "ValidationException", "Message": "Invalid input"}
            },
            operation_name="StartExecution",
        )
        process._step_machine.start_execution.side_effect = error

        result = process.start(
            "test_id", "test_token", sample_invasion, sample_files, "Ladder"
        )

        assert "Failed to call process step function:" in result
        assert "ValidationException" in result

    def test_start_logs_operations(self, process, sample_invasion, sample_files):
        """Test that start method logs operations correctly."""
        process.start("test_id", "test_token", sample_invasion, sample_files, "Ladder")

        # Verify logging calls were made
        assert process._logger.info.call_count >= 2  # Start and completion logs

    def test_process_types_coverage(self, process, sample_invasion, sample_files):
        """Test that all expected process types are handled."""
        valid_types = ["Ladder", "Roster"]

        for process_type in valid_types:
            # Reset mock for each test
            process._step_machine.start_execution.reset_mock()

            result = process.start(
                "test_id", "test_token", sample_invasion, sample_files, process_type
            )

            assert result == "In Progress: Downloading and processing screenshot(s)"
            process._step_machine.start_execution.assert_called_once()

    def test_invasion_path_generation(self, process, sample_invasion, sample_files):
        """Test that invasion paths are generated correctly."""
        # Test ladder path
        process.start("test_id", "test_token", sample_invasion, sample_files, "Ladder")
        call_args = process._step_machine.start_execution.call_args
        input_data = json.loads(call_args[1]["input"])
        assert input_data["folder"] == "ladders/20240301-bw/"

        # Reset mock and test roster path
        process._step_machine.start_execution.reset_mock()
        process.start("test_id", "test_token", sample_invasion, sample_files, "Roster")
        call_args = process._step_machine.start_execution.call_args
        input_data = json.loads(call_args[1]["input"])
        assert input_data["folder"] == "roster/20240301-bw/"
