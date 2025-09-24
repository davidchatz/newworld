#!/usr/bin/env python3
"""
Test script for image preprocessing - displays before/after images side by side
Usage: python test_image_processing.py <image_path> [contrast] [saturation]
"""

import sys
import os
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import matplotlib.pyplot as plt

def process_image(image_path, contrast_factor=1.5, saturation_factor=0.7):
    """Apply the same processing as ImagePreprocessor"""
    with Image.open(image_path) as img:
        print(f"Original image mode: {img.mode}")

        # Store original
        original = img.copy()

        # Convert to RGB first, then grayscale for proper processing
        if img.mode != 'RGB':
            img = img.convert('RGB')
        print(f"After RGB conversion: {img.mode}")

        # Convert to grayscale (L mode = single channel luminance)
        img = ImageOps.grayscale(img)
        print(f"After grayscale conversion: {img.mode}")

        # Apply threshold to get pure black/white
        threshold = 128
        img = img.point(lambda p: 255 if p > threshold else 0)
        print(f"After thresholding: {img.mode}")

        # Apply autocontrast for better histogram distribution
        img = ImageOps.autocontrast(img, cutoff=(60,0))
        print(f"After autocontrast: {img.mode}")

        # Resize (upscale) for better OCR
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
        print(f"After resize: {img.mode}")

        # Sharpen for OCR
        img = img.filter(ImageFilter.SHARPEN)
        print(f"Final processed image mode: {img.mode}")

        # Convert to Greyscale
        # img = img.convert('L', dither=Dither.NONE)
        #img = ImageOps.grayscale(img)

        # Decrease saturation
        # enhancer = ImageEnhance.Color(img)
        # img = enhancer.enhance(saturation_factor)

        # Use ImageOps.autocontrast to adjust the histogram
        # img = ImageOps.autocontrast(img, cutoff=(50,0))
        

        
        # img = img.filter(ImageFilter.SHARPEN)

        # img = img.filter(ImageFilter.MedianFilter(size=3))

        # Increase contrast
        # enhancer = ImageEnhance.Contrast(img)
        # img = enhancer.enhance(contrast_factor)

        return original, img

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_image_processing.py <image_path> [contrast] [saturation]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    contrast = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5
    saturation = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7
    
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} not found")
        sys.exit(1)
    
    print(f"Processing {image_path} with contrast={contrast}, saturation={saturation}")
    
    original, processed = process_image(image_path, contrast, saturation)
    
    # Display side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

    ax1.imshow(original)
    ax1.set_title('Original')
    ax1.axis('off')

    # Display processed image in grayscale colormap
    ax2.imshow(processed, cmap='gray', vmin=0, vmax=255)
    ax2.set_title(f'Processed (Black/White, Mode: {processed.mode})')
    ax2.axis('off')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()