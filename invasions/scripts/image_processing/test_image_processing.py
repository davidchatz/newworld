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
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Store original
        original = img.copy()
        
        # Convert to Greyscale
        # img = img.convert('L', dither=Dither.NONE)
        #img = ImageOps.grayscale(img)

        # Decrease saturation
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(saturation_factor)

        # Use ImageOps.autocontrast to adjust the histogram
        img = ImageOps.autocontrast(img, cutoff=(50,0))
        

        
        img = img.filter(ImageFilter.SHARPEN)

        # img = img.filter(ImageFilter.MedianFilter(size=3))

        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast_factor)

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
    
    ax2.imshow(processed)
    ax2.set_title(f'Processed (C:{contrast}, S:{saturation})')
    ax2.axis('off')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()