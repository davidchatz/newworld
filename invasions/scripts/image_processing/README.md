# Image Processing Test Script

Test script for experimenting with image preprocessing settings used in the invasion bot.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Test with defaults (contrast=1.5, saturation=0.7)
python test_image_processing.py path/to/your/image.png

# Test with custom settings
python test_image_processing.py path/to/your/image.png 2.0 0.5
```

## Examples

```bash
# High contrast, very low saturation
python test_image_processing.py screenshot.png 2.5 0.3

# Moderate contrast, normal saturation  
python test_image_processing.py screenshot.png 1.2 0.8

# Extreme processing
python test_image_processing.py screenshot.png 3.0 0.1
```

The script displays original and processed images side by side to help you find optimal settings before updating the SAM template parameters.