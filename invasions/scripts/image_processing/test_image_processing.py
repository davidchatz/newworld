#!/usr/bin/env python3
"""
Test script for image preprocessing - displays before/after images side by side
Usage: python test_image_processing.py <image_path> [options]
"""

import argparse
import os
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import matplotlib.pyplot as plt

def process_image(image_path, bw_threshold=128, autocontrast_cutoff=None,
                  sharpen=True, upscale=True, invert=True,
                  contrast_factor=None, saturation_factor=0.7):
    """Apply configurable image processing"""
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
        img = img.point(lambda p: 255 if p > bw_threshold else 0)
        print(f"After thresholding (threshold={bw_threshold}): {img.mode}")

        # Apply autocontrast for better histogram distribution (if specified)
        if autocontrast_cutoff is not None:
            img = ImageOps.autocontrast(img, cutoff=autocontrast_cutoff)
            print(f"After autocontrast (cutoff={autocontrast_cutoff}): {img.mode}")

        # Apply contrast enhancement (if specified)
        if contrast_factor is not None:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast_factor)
            print(f"After contrast enhancement (factor={contrast_factor}): {img.mode}")

        # Resize (upscale) for better OCR
        if upscale:
            img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
            print(f"After resize: {img.mode}")

        # Sharpen for OCR
        if sharpen:
            img = img.filter(ImageFilter.SHARPEN)
            print(f"After sharpen: {img.mode}")

        # Invert
        if invert:
            img = ImageOps.invert(img)
            print(f"After invert: {img.mode}")

        print(f"Final processed image mode: {img.mode}")

        return original, img

def main():
    parser = argparse.ArgumentParser(
        description='Test image preprocessing with configurable parameters'
    )

    # Required argument
    parser.add_argument('image_path', help='Path to the image file to process')

    # Image enhancement parameters
    parser.add_argument('--contrast-factor', type=float, default=None,
                       help='Contrast enhancement factor (disabled by default)')
    parser.add_argument('--saturation-factor', type=float, default=0.7,
                       help='Saturation factor (default: 0.7, currently unused)')

    # Black & white threshold
    parser.add_argument('--bw-threshold', type=int, default=128,
                       help='Black/white threshold value 0-255 (default: 128)')

    # Autocontrast parameters
    parser.add_argument('--autocontrast-cutoff', type=int, nargs=2, default=None,
                       metavar=('LOW', 'HIGH'),
                       help='Autocontrast cutoff percentages (disabled by default, example: 60 0)')

    # Boolean flags for optional processing steps
    parser.add_argument('--sharpen', action='store_true', default=True,
                       help='Apply sharpening filter (default: enabled)')
    parser.add_argument('--no-sharpen', action='store_false', dest='sharpen',
                       help='Disable sharpening filter')

    parser.add_argument('--upscale', action='store_true', default=True,
                       help='Upscale image 2x for better OCR (default: enabled)')
    parser.add_argument('--no-upscale', action='store_false', dest='upscale',
                       help='Disable upscaling')

    parser.add_argument('--invert', action='store_true', default=True,
                       help='Invert the image colors (default: enabled)')
    parser.add_argument('--no-invert', action='store_false', dest='invert',
                       help='Disable color inversion')

    args = parser.parse_args()

    if not os.path.exists(args.image_path):
        print(f"Error: File {args.image_path} not found")
        return 1

    print(f"Processing {args.image_path}")
    print(f"  Contrast factor: {args.contrast_factor if args.contrast_factor is not None else 'disabled'}")
    print(f"  Saturation factor: {args.saturation_factor} (unused)")
    print(f"  B/W threshold: {args.bw_threshold}")
    print(f"  Autocontrast cutoff: {args.autocontrast_cutoff if args.autocontrast_cutoff is not None else 'disabled'}")
    print(f"  Sharpen: {args.sharpen}")
    print(f"  Upscale: {args.upscale}")
    print(f"  Invert: {args.invert}")
    print()

    original, processed = process_image(
        args.image_path,
        bw_threshold=args.bw_threshold,
        autocontrast_cutoff=tuple(args.autocontrast_cutoff) if args.autocontrast_cutoff is not None else None,
        sharpen=args.sharpen,
        upscale=args.upscale,
        invert=args.invert,
        contrast_factor=args.contrast_factor,
        saturation_factor=args.saturation_factor
    )
    
    # Display side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    ax1.imshow(original)
    ax1.set_title('Original')
    ax1.axis('off')

    # Build title with all parameters
    param_lines = [
        f'Processed (Mode: {processed.mode})',
        f'Threshold: {args.bw_threshold}',
        f'Autocontrast: {args.autocontrast_cutoff if args.autocontrast_cutoff else "off"} | Contrast: {args.contrast_factor if args.contrast_factor else "off"}',
        f'Sharpen: {args.sharpen} | Upscale: {args.upscale} | Invert: {args.invert}'
    ]

    # Display processed image in grayscale colormap
    ax2.imshow(processed, cmap='gray', vmin=0, vmax=255)
    ax2.set_title('\n'.join(param_lines), fontsize=10)
    ax2.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()