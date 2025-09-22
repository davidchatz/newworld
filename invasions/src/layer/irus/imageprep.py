from PIL import Image, ImageEnhance, ImageOps
import io
from .environ import IrusResources

logger = IrusResources.logger()
s3 = IrusResources.s3()

class ImagePreprocessor:
    
    def __init__(self, contrast_factor=None, saturation_factor=None):
        self.contrast_factor = contrast_factor or IrusResources.image_contrast_factor()
        self.saturation_factor = saturation_factor or IrusResources.image_saturation_factor()
    
    def preprocess_s3_image(self, bucket: str, key: str) -> str:
        """Download, preprocess, and upload image back to S3. Returns new key."""
        logger.info(f'Preprocessing image {bucket}/{key}')
        
        # Download image from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        image_data = response['Body'].read()
        
        # Process image
        processed_data = self._process_image(image_data)
        
        # Upload processed image with new key
        processed_key = key.replace('.png', '_processed.png')
        s3.put_object(Bucket=bucket, Key=processed_key, Body=processed_data)
        
        logger.info(f'Processed image saved as {bucket}/{processed_key}')
        return processed_key
    
    def _process_image(self, image_data: bytes) -> bytes:
        """Apply contrast and saturation adjustments to image."""
        with Image.open(io.BytesIO(image_data)) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Decrease saturation
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(self.saturation_factor)
            
            img = ImageOps.autocontrast(img, cutoff=(50,0))

            # Increase contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self.contrast_factor)
            
            # Save to bytes
            output = io.BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()