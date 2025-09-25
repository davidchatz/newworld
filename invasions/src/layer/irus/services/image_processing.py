"""Image processing service for preprocessing screenshots before OCR."""

import io

from PIL import Image, ImageFilter, ImageOps

from ..container import IrusContainer


class ImageProcessingService:
    """Service for preprocessing images to improve OCR accuracy."""

    def __init__(self, container: IrusContainer | None = None):
        """Initialize the image processing service.

        Args:
            container: Dependency injection container. Uses default if None.
        """
        self._container = container or IrusContainer.default()
        self._logger = self._container.logger()
        self._s3 = self._container.s3()

        # Get image processing parameters from configuration
        self._contrast_factor = self._container.image_contrast_factor()
        self._saturation_factor = self._container.image_saturation_factor()

    def preprocess_s3_image(self, bucket: str, key: str) -> str:
        """Download, preprocess, and upload image back to S3.

        Args:
            bucket: S3 bucket name
            key: Original image key

        Returns:
            New key for the processed image

        Raises:
            ClientError: If S3 operations fail
        """
        self._logger.info(f"Preprocessing image {bucket}/{key}")

        # Download image from S3
        response = self._s3.get_object(Bucket=bucket, Key=key)
        image_data = response["Body"].read()

        # Process image
        processed_data = self.process_image_data(image_data)

        # Upload processed image with new key
        processed_key = self._generate_processed_key(key)
        self._s3.put_object(
            Bucket=bucket,
            Key=processed_key,
            Body=processed_data,
            ContentType="image/png",
        )

        self._logger.info(f"Processed image saved as {bucket}/{processed_key}")
        return processed_key

    def process_image_data(self, image_data: bytes) -> bytes:
        """Apply preprocessing pipeline to image data.

        Args:
            image_data: Raw image bytes

        Returns:
            Processed image bytes in PNG format

        Raises:
            PIL.UnidentifiedImageError: If image format is not supported
        """
        with Image.open(io.BytesIO(image_data)) as img:
            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")

            processed_img = self._apply_preprocessing_pipeline(img)

            # Save to bytes
            output = io.BytesIO()
            processed_img.save(output, format="PNG")
            return output.getvalue()

    def _apply_preprocessing_pipeline(self, img: Image.Image) -> Image.Image:
        """Apply the complete preprocessing pipeline to an image.

        Args:
            img: PIL Image object

        Returns:
            Processed PIL Image object
        """
        # 1. Convert to grayscale
        img = ImageOps.grayscale(img)

        # 2. Apply threshold to create binary image
        img = self._apply_threshold(img)

        # 3. Auto-contrast adjustment
        img = ImageOps.autocontrast(img, cutoff=(60, 0))

        # 4. Upscale for better OCR
        img = self._upscale_image(img)

        # 5. Sharpen the image
        img = img.filter(ImageFilter.SHARPEN)

        # 6. Invert colors (white text on black background)
        img = ImageOps.invert(img)

        return img

    def _apply_threshold(self, img: Image.Image, threshold: int = 128) -> Image.Image:
        """Apply binary threshold to image.

        Args:
            img: Grayscale PIL Image
            threshold: Threshold value (0-255)

        Returns:
            Binary image with threshold applied
        """
        return img.point(lambda p: p > threshold and 255)

    def _upscale_image(self, img: Image.Image, scale_factor: int = 2) -> Image.Image:
        """Upscale image using high-quality resampling.

        Args:
            img: PIL Image to upscale
            scale_factor: Scaling factor

        Returns:
            Upscaled image
        """
        new_size = (img.width * scale_factor, img.height * scale_factor)
        return img.resize(new_size, Image.LANCZOS)

    def _generate_processed_key(self, original_key: str) -> str:
        """Generate key for processed image.

        Args:
            original_key: Original image S3 key

        Returns:
            New key with processed suffix
        """
        if original_key.lower().endswith(".png"):
            return original_key.replace(".png", "_processed.png")
        elif original_key.lower().endswith(".jpg") or original_key.lower().endswith(
            ".jpeg"
        ):
            return original_key.rsplit(".", 1)[0] + "_processed.png"
        else:
            return f"{original_key}_processed.png"

    def get_image_dimensions(self, bucket: str, key: str) -> tuple[int, int]:
        """Get dimensions of an image stored in S3.

        Args:
            bucket: S3 bucket name
            key: Image key

        Returns:
            Tuple of (width, height)

        Raises:
            ClientError: If S3 operations fail
            PIL.UnidentifiedImageError: If image format is not supported
        """
        response = self._s3.get_object(Bucket=bucket, Key=key)
        image_data = response["Body"].read()

        with Image.open(io.BytesIO(image_data)) as img:
            return img.size

    def create_image_preview(
        self, bucket: str, key: str, max_size: tuple[int, int] = (300, 300)
    ) -> bytes:
        """Create a thumbnail preview of an image.

        Args:
            bucket: S3 bucket name
            key: Image key
            max_size: Maximum dimensions for preview

        Returns:
            Preview image bytes in PNG format

        Raises:
            ClientError: If S3 operations fail
            PIL.UnidentifiedImageError: If image format is not supported
        """
        response = self._s3.get_object(Bucket=bucket, Key=key)
        image_data = response["Body"].read()

        with Image.open(io.BytesIO(image_data)) as img:
            img.thumbnail(max_size, Image.LANCZOS)

            output = io.BytesIO()
            img.save(output, format="PNG")
            return output.getvalue()
