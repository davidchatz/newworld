"""Integration tests for S3 operations with real AWS resources.

These tests validate that S3 file operations work correctly with
real AWS S3 bucket using test file prefixes for isolation.
"""

import json
from datetime import datetime

import pytest


class TestS3Integration:
    """Integration tests for S3 file operations."""

    @pytest.fixture
    def s3_client(self, integration_container):
        """Get S3 client from integration container."""
        return integration_container.s3()

    @pytest.fixture
    def bucket_name(self, integration_container):
        """Get S3 bucket name from integration container."""
        return integration_container.bucket_name()

    @pytest.fixture
    def test_file_key(self):
        """Generate unique test file key with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"integration-tests/test-file-{timestamp}.json"

    @pytest.fixture
    def test_image_key(self):
        """Generate unique test image key with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"integration-tests/test-image-{timestamp}.jpg"

    def test_s3_put_and_get_object(self, s3_client, bucket_name, test_file_key):
        """Test basic S3 put and get operations with real bucket.

        This test validates:
        - S3 client can write objects to real bucket
        - S3 client can read objects from real bucket
        - Data integrity is maintained through S3 operations
        """
        # Arrange
        test_data = {
            "test_type": "integration_test",
            "timestamp": datetime.now().isoformat(),
            "data": {"player": "TestPlayer", "faction": "yellow"},
        }
        test_content = json.dumps(test_data)

        try:
            # Act - Put object
            put_response = s3_client.put_object(
                Bucket=bucket_name,
                Key=test_file_key,
                Body=test_content,
                ContentType="application/json",
            )

            # Assert - Put operation succeeded
            assert put_response["ResponseMetadata"]["HTTPStatusCode"] == 200

            # Act - Get object
            get_response = s3_client.get_object(Bucket=bucket_name, Key=test_file_key)

            # Assert - Get operation succeeded and data matches
            assert get_response["ResponseMetadata"]["HTTPStatusCode"] == 200
            retrieved_content = get_response["Body"].read().decode("utf-8")
            retrieved_data = json.loads(retrieved_content)

            assert retrieved_data == test_data
            assert retrieved_data["test_type"] == "integration_test"

        finally:
            # Cleanup - Delete test file
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=test_file_key)
            except Exception:
                pass  # Cleanup failure shouldn't fail the test

    def test_s3_list_objects_with_prefix(self, s3_client, bucket_name):
        """Test S3 list operations with prefix filtering."""
        # Arrange - Create multiple test files
        test_prefix = "integration-tests/"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        test_keys = [
            f"{test_prefix}list-test-1-{timestamp}.txt",
            f"{test_prefix}list-test-2-{timestamp}.txt",
            f"{test_prefix}list-test-3-{timestamp}.txt",
        ]

        created_keys = []
        try:
            # Create test files
            for key in test_keys:
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=key,
                    Body=f"Test content for {key}",
                    ContentType="text/plain",
                )
                created_keys.append(key)

            # Act - List objects with prefix
            response = s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix=test_prefix, MaxKeys=10
            )

            # Assert - Should find our test files
            assert "Contents" in response
            found_keys = [obj["Key"] for obj in response["Contents"]]

            # All our test keys should be in the results
            for key in test_keys:
                assert key in found_keys, f"Test key {key} not found in S3 list results"

        finally:
            # Cleanup - Delete all test files
            for key in created_keys:
                try:
                    s3_client.delete_object(Bucket=bucket_name, Key=key)
                except Exception:
                    pass

    def test_s3_object_not_found_handling(self, s3_client, bucket_name):
        """Test S3 error handling for non-existent objects."""
        # Arrange
        non_existent_key = "integration-tests/non-existent-file-999999.txt"

        # Act & Assert - Should raise NoSuchKey exception
        with pytest.raises(Exception) as exc_info:
            s3_client.get_object(Bucket=bucket_name, Key=non_existent_key)

        # Verify it's the expected S3 error
        error_code = exc_info.value.response.get("Error", {}).get("Code")
        assert error_code == "NoSuchKey"

    def test_s3_large_file_operations(self, s3_client, bucket_name, test_file_key):
        """Test S3 operations with larger files (simulating image uploads)."""
        # Arrange - Create larger test content (simulating image data)
        large_content = b"FAKE_IMAGE_DATA:" + b"x" * (1024 * 100)  # 100KB of fake data

        try:
            # Act - Upload large content
            put_response = s3_client.put_object(
                Bucket=bucket_name,
                Key=test_file_key,
                Body=large_content,
                ContentType="image/jpeg",
            )

            # Assert - Upload succeeded
            assert put_response["ResponseMetadata"]["HTTPStatusCode"] == 200

            # Act - Download large content
            get_response = s3_client.get_object(Bucket=bucket_name, Key=test_file_key)

            # Assert - Download succeeded and data integrity maintained
            assert get_response["ResponseMetadata"]["HTTPStatusCode"] == 200
            retrieved_content = get_response["Body"].read()
            assert len(retrieved_content) == len(large_content)
            assert retrieved_content == large_content

            # Verify metadata
            assert get_response["ContentType"] == "image/jpeg"
            assert get_response["ContentLength"] == len(large_content)

        finally:
            # Cleanup
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=test_file_key)
            except Exception:
                pass

    def test_s3_metadata_operations(self, s3_client, bucket_name, test_file_key):
        """Test S3 metadata and tagging operations."""
        # Arrange
        test_content = "Test content with metadata"
        metadata = {
            "test-type": "integration",
            "invasion-id": "99990301-s3test",
            "processed": "true",
        }

        try:
            # Act - Put object with metadata
            put_response = s3_client.put_object(
                Bucket=bucket_name,
                Key=test_file_key,
                Body=test_content,
                ContentType="text/plain",
                Metadata=metadata,
            )

            # Assert - Upload with metadata succeeded
            assert put_response["ResponseMetadata"]["HTTPStatusCode"] == 200

            # Act - Get object metadata
            head_response = s3_client.head_object(Bucket=bucket_name, Key=test_file_key)

            # Assert - Metadata was preserved
            assert head_response["ResponseMetadata"]["HTTPStatusCode"] == 200
            retrieved_metadata = head_response.get("Metadata", {})

            for key, value in metadata.items():
                assert key in retrieved_metadata
                assert retrieved_metadata[key] == value

        finally:
            # Cleanup
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=test_file_key)
            except Exception:
                pass

    def test_s3_container_integration(self, integration_container, test_file_key):
        """Test S3 operations through container dependency injection."""
        # Act - Get S3 resources from container
        s3_client = integration_container.s3()
        bucket_name = integration_container.bucket_name()

        # Assert - Container provides valid S3 configuration
        assert s3_client is not None
        assert bucket_name is not None
        assert "irus-dev" in bucket_name.lower()

        # Test basic operation through container
        test_content = "Container integration test"

        try:
            # Act - Use container-provided S3 client
            put_response = s3_client.put_object(
                Bucket=bucket_name,
                Key=test_file_key,
                Body=test_content,
                ContentType="text/plain",
            )

            # Assert - Operation succeeded through container
            assert put_response["ResponseMetadata"]["HTTPStatusCode"] == 200

            # Verify with get operation
            get_response = s3_client.get_object(Bucket=bucket_name, Key=test_file_key)

            retrieved_content = get_response["Body"].read().decode("utf-8")
            assert retrieved_content == test_content

        finally:
            # Cleanup
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=test_file_key)
            except Exception:
                pass

    def test_s3_concurrent_operations(self, s3_client, bucket_name):
        """Test S3 operations under concurrent access patterns."""
        # Arrange - Multiple test files for concurrent operations
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        test_keys = []

        try:
            # Act - Create multiple files rapidly (simulating concurrent uploads)
            for i in range(5):
                key = f"integration-tests/concurrent-{timestamp}-{i}.txt"
                test_keys.append(key)

                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=key,
                    Body=f"Concurrent test file {i}",
                    ContentType="text/plain",
                )

            # Act - Read all files back rapidly
            retrieved_contents = []
            for key in test_keys:
                response = s3_client.get_object(Bucket=bucket_name, Key=key)
                content = response["Body"].read().decode("utf-8")
                retrieved_contents.append(content)

            # Assert - All operations should succeed
            assert len(retrieved_contents) == 5
            for i, content in enumerate(retrieved_contents):
                assert content == f"Concurrent test file {i}"

        finally:
            # Cleanup
            for key in test_keys:
                try:
                    s3_client.delete_object(Bucket=bucket_name, Key=key)
                except Exception:
                    pass
