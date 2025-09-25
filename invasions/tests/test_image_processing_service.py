"""Tests for Image processing service."""

import io
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError
from irus.container import IrusContainer
from irus.services.image_processing import ImageProcessingService
from PIL import Image


class TestImageProcessingService:
    """Test suite for ImageProcessingService class."""

    @pytest.fixture
    def container(self):
        """Create test container with mocked dependencies."""
        mock_container = IrusContainer.create_test()
        mock_container.image_contrast_factor = Mock(return_value=1.2)
        mock_container.image_saturation_factor = Mock(return_value=0.8)

        # Mock S3 client
        mock_s3 = Mock()
        mock_container.s3 = Mock(return_value=mock_s3)

        return mock_container

    @pytest.fixture
    def service(self, container):
        """Create ImageProcessingService instance with test container."""
        return ImageProcessingService(container)

    @pytest.fixture
    def sample_image_data(self):
        """Create sample image data for testing."""
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()

    @pytest.fixture
    def mock_s3_response(self, sample_image_data):
        """Create mock S3 response."""
        mock_response = {"Body": Mock()}
        mock_response["Body"].read.return_value = sample_image_data
        return mock_response

    def test_init(self, container):
        """Test ImageProcessingService initialization."""
        service = ImageProcessingService(container)

        assert service._container is container
        assert service._logger is not None
        assert service._s3 is not None
        assert service._contrast_factor == 1.2
        assert service._saturation_factor == 0.8

    def test_init_default_container(self):
        """Test ImageProcessingService initialization with default container."""
        with patch.object(IrusContainer, "default") as mock_default:
            mock_container = Mock(spec=IrusContainer)
            mock_container.logger.return_value = Mock()
            mock_container.s3.return_value = Mock()
            mock_container.image_contrast_factor.return_value = 1.0
            mock_container.image_saturation_factor.return_value = 1.0
            mock_default.return_value = mock_container

            service = ImageProcessingService()

            assert service._container is mock_container
            mock_default.assert_called_once()

    def test_preprocess_s3_image_success(self, service, mock_s3_response):
        """Test preprocessing S3 image successfully."""
        service._s3.get_object.return_value = mock_s3_response
        service._s3.put_object.return_value = {}

        result = service.preprocess_s3_image("test-bucket", "test-image.png")

        assert result == "test-image_processed.png"

        # Verify S3 operations
        service._s3.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test-image.png"
        )
        service._s3.put_object.assert_called_once()

        # Check put_object call arguments
        put_call = service._s3.put_object.call_args
        assert put_call[1]["Bucket"] == "test-bucket"
        assert put_call[1]["Key"] == "test-image_processed.png"
        assert put_call[1]["ContentType"] == "image/png"
        assert isinstance(put_call[1]["Body"], bytes)

    def test_preprocess_s3_image_jpg_extension(self, service, mock_s3_response):
        """Test preprocessing S3 image with JPG extension."""
        service._s3.get_object.return_value = mock_s3_response
        service._s3.put_object.return_value = {}

        result = service.preprocess_s3_image("test-bucket", "test-image.jpg")

        assert result == "test-image_processed.png"

    def test_preprocess_s3_image_s3_error(self, service):
        """Test handling S3 errors during preprocessing."""
        error = ClientError(
            error_response={"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
            operation_name="GetObject",
        )
        service._s3.get_object.side_effect = error

        with pytest.raises(ClientError):
            service.preprocess_s3_image("test-bucket", "missing-image.png")

    def test_process_image_data(self, service, sample_image_data):
        """Test processing raw image data."""
        result = service.process_image_data(sample_image_data)

        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify the result is valid PNG data
        processed_img = Image.open(io.BytesIO(result))
        assert processed_img.format == "PNG"

    def test_process_image_data_convert_mode(self, service):
        """Test processing image data with mode conversion."""
        # Create RGBA image that needs conversion
        img = Image.new("RGBA", (100, 100), color=(128, 128, 128, 255))
        output = io.BytesIO()
        img.save(output, format="PNG")
        rgba_data = output.getvalue()

        result = service.process_image_data(rgba_data)

        assert isinstance(result, bytes)
        processed_img = Image.open(io.BytesIO(result))
        assert processed_img.format == "PNG"

    def test_apply_preprocessing_pipeline(self, service):
        """Test the complete preprocessing pipeline."""
        # Create test image
        img = Image.new("RGB", (50, 50), color=(100, 150, 200))

        result = service._apply_preprocessing_pipeline(img)

        # Should be grayscale mode after processing
        assert result.mode == "L"  # Grayscale mode
        # Should be upscaled (2x)
        assert result.size == (100, 100)

    def test_apply_threshold(self, service):
        """Test threshold application."""
        # Create grayscale image
        img = Image.new("L", (100, 100), color=150)

        # Test with threshold 128 (default)
        result = service._apply_threshold(img, 128)
        # Pixels with value 150 > 128, so should become 255
        assert result.getpixel((50, 50)) == 255

        # Test with higher threshold
        result = service._apply_threshold(img, 200)
        # Pixels with value 150 < 200, so should become 0
        assert result.getpixel((50, 50)) == 0

    def test_upscale_image(self, service):
        """Test image upscaling."""
        img = Image.new("L", (50, 50), color=128)

        # Test 2x upscaling (default)
        result = service._upscale_image(img, 2)
        assert result.size == (100, 100)

        # Test 3x upscaling
        result = service._upscale_image(img, 3)
        assert result.size == (150, 150)

    def test_generate_processed_key(self, service):
        """Test processed key generation."""
        # PNG extension
        assert service._generate_processed_key("image.png") == "image_processed.png"

        # JPG extension
        assert service._generate_processed_key("image.jpg") == "image_processed.png"

        # JPEG extension
        assert service._generate_processed_key("image.jpeg") == "image_processed.png"

        # No extension
        assert service._generate_processed_key("image") == "image_processed.png"

        # Complex path
        assert (
            service._generate_processed_key("folder/subfolder/image.png")
            == "folder/subfolder/image_processed.png"
        )

    def test_get_image_dimensions(self, service, mock_s3_response):
        """Test getting image dimensions from S3."""
        service._s3.get_object.return_value = mock_s3_response

        width, height = service.get_image_dimensions("test-bucket", "test-image.png")

        assert width == 100
        assert height == 100
        service._s3.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="test-image.png"
        )

    def test_get_image_dimensions_s3_error(self, service):
        """Test handling S3 errors when getting dimensions."""
        error = ClientError(
            error_response={
                "Error": {"Code": "AccessDenied", "Message": "Access denied"}
            },
            operation_name="GetObject",
        )
        service._s3.get_object.side_effect = error

        with pytest.raises(ClientError):
            service.get_image_dimensions("test-bucket", "test-image.png")

    def test_create_image_preview(self, service, mock_s3_response):
        """Test creating image preview."""
        service._s3.get_object.return_value = mock_s3_response

        preview_data = service.create_image_preview("test-bucket", "test-image.png")

        assert isinstance(preview_data, bytes)
        assert len(preview_data) > 0

        # Verify the preview is valid PNG data
        preview_img = Image.open(io.BytesIO(preview_data))
        assert preview_img.format == "PNG"

        # Should be thumbnail size (smaller than original)
        assert preview_img.size[0] <= 300
        assert preview_img.size[1] <= 300

    def test_create_image_preview_custom_size(self, service, mock_s3_response):
        """Test creating image preview with custom size."""
        service._s3.get_object.return_value = mock_s3_response

        preview_data = service.create_image_preview(
            "test-bucket", "test-image.png", max_size=(50, 50)
        )

        preview_img = Image.open(io.BytesIO(preview_data))
        assert preview_img.size[0] <= 50
        assert preview_img.size[1] <= 50

    def test_logging_operations(self, service, mock_s3_response):
        """Test that operations are logged correctly."""
        service._s3.get_object.return_value = mock_s3_response
        service._s3.put_object.return_value = {}

        service.preprocess_s3_image("test-bucket", "test-image.png")

        # Verify logging calls were made
        assert service._logger.info.call_count >= 2  # Start and completion logs

    @patch("PIL.Image.open")
    def test_process_invalid_image_data(self, mock_open, service):
        """Test handling invalid image data."""
        from PIL import UnidentifiedImageError

        mock_open.side_effect = UnidentifiedImageError("Cannot identify image file")

        with pytest.raises(UnidentifiedImageError):
            service.process_image_data(b"invalid image data")

    def test_pipeline_components_called(self, service):
        """Test that all pipeline components are called."""
        img = Image.new("RGB", (50, 50), color=(128, 128, 128))

        with (
            patch.object(service, "_apply_threshold") as mock_threshold,
            patch.object(service, "_upscale_image") as mock_upscale,
        ):
            # Set up return values to continue the pipeline
            mock_threshold.return_value = img.convert("L")
            mock_upscale.return_value = img.convert("L").resize((100, 100))

            service._apply_preprocessing_pipeline(img)

            # Verify pipeline methods were called
            mock_threshold.assert_called_once()
            mock_upscale.assert_called_once()

    def test_contrast_and_saturation_factors_used(self, container):
        """Test that contrast and saturation factors are properly loaded."""
        service = ImageProcessingService(container)

        assert service._contrast_factor == 1.2
        assert service._saturation_factor == 0.8
        container.image_contrast_factor.assert_called_once()
        container.image_saturation_factor.assert_called_once()
