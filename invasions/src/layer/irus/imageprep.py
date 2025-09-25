"""Backward compatibility facade for ImagePreprocessor.

This module provides backward compatibility for the legacy ImagePreprocessor class
while internally using the new ImageProcessingService architecture.

DEPRECATED: This facade is provided for backward compatibility only.
New code should use irus.services.image_processing.ImageProcessingService directly.
"""

import warnings

from .services.image_processing import ImageProcessingService

# Issue deprecation warning when this module is imported
warnings.warn(
    "irus.imageprep module is deprecated. Use irus.services.image_processing.ImageProcessingService instead.",
    DeprecationWarning,
    stacklevel=2,
)


class ImagePreprocessor:
    """Legacy ImagePreprocessor class for backward compatibility.

    This class wraps the new ImageProcessingService implementation to maintain
    backward compatibility with existing code.

    DEPRECATED: Use irus.services.image_processing.ImageProcessingService instead.
    """

    def __init__(self, contrast_factor=None, saturation_factor=None):
        """Initialize the legacy image preprocessor.

        Args:
            contrast_factor: Contrast adjustment factor (legacy parameter, now configured via environment)
            saturation_factor: Saturation adjustment factor (legacy parameter, now configured via environment)

        Note:
            The contrast_factor and saturation_factor parameters are maintained for
            backward compatibility but are now ignored. Configuration is handled
            through the container's environment settings.
        """
        # Create new service instance - parameters are now configured via container
        self._service = ImageProcessingService()

        # Store legacy parameters for compatibility (though they're not used)
        self.contrast_factor = contrast_factor
        self.saturation_factor = saturation_factor

    def preprocess_s3_image(self, bucket: str, key: str) -> str:
        """Download, preprocess, and upload image back to S3 (legacy API).

        Args:
            bucket: S3 bucket name
            key: Original image key

        Returns:
            New key for the processed image
        """
        return self._service.preprocess_s3_image(bucket=bucket, key=key)

    def _process_image(self, image_data: bytes) -> bytes:
        """Apply preprocessing to image data (legacy API).

        Args:
            image_data: Raw image bytes

        Returns:
            Processed image bytes

        Note:
            This method is deprecated. New code should use
            ImageProcessingService.process_image_data() directly.
        """
        return self._service.process_image_data(image_data)
