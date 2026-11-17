"""Synthetic Watermarked Test Document Generator for OCR Pipeline Testing.

Generates reproducible synthetic identity cards, driver licenses, and passports
with explicit synthetic test watermarks to prevent any real-world credential leakage.
"""

import io
from typing import Any, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFilter

WATERMARK_TEXT = "SYNTHETIC TEST DOCUMENT - NOT REAL ID - FOR TESTING ONLY"

SYNTHETIC_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "SYNTH_NAT_ID_V1": {
        "title": "NATIONAL IDENTITY CARD",
        "fields": {
            "document_number": "NAT-98421074",
            "full_name": "Jane Synth Citizen",
            "date_of_birth": "1988-04-12",
            "issue_date": "2020-05-15",
            "expiry_date": "2030-05-15",
            "issuing_authority": "National Identity Authority",
            "country": "IND",
        },
        "background_color": (230, 240, 255),
        "primary_color": (20, 50, 120),
    },
    "SYNTH_DL_V1": {
        "title": "DRIVING LICENCE",
        "fields": {
            "document_number": "DL-TN-2021-998811",
            "full_name": "John Synth Driver",
            "date_of_birth": "1992-09-21",
            "issue_date": "2021-02-10",
            "expiry_date": "2031-02-10",
            "vehicle_classes": "LMV, MCWG",
            "issuing_authority": "Transport Department",
            "country": "IND",
        },
        "background_color": (245, 250, 235),
        "primary_color": (30, 90, 40),
    },
    "SYNTH_PASSPORT_V1": {
        "title": "PASSPORT",
        "fields": {
            "document_number": "P9823411",
            "full_name": "Alex Synth Traveler",
            "date_of_birth": "1995-11-03",
            "issue_date": "2018-07-01",
            "expiry_date": "2028-07-01",
            "mrz_line1": "P<INDSYNTH<<ALEX<<<<<<<<<<<<<<<<<<<<<<<<<",
            "mrz_line2": "P9823411<7IND9511039M2807018<<<<<<<<<<<<<<2",
            "issuing_authority": "Passport Office",
            "country": "IND",
        },
        "background_color": (250, 245, 240),
        "primary_color": (70, 30, 80),
    },
    "SYNTH_EXPIRED_NAT_ID": {
        "title": "NATIONAL IDENTITY CARD (EXPIRED)",
        "fields": {
            "document_number": "NAT-11223344",
            "full_name": "Marcus Old Synth",
            "date_of_birth": "1975-01-10",
            "issue_date": "2010-01-01",
            "expiry_date": "2020-01-01",
            "issuing_authority": "National Identity Authority",
            "country": "IND",
        },
        "background_color": (240, 240, 240),
        "primary_color": (80, 80, 80),
    },
    "SYNTH_AADHAAR_V1": {
        "title": "GOVERNMENT OF INDIA - UNIQUE IDENTIFICATION AUTHORITY",
        "fields": {
            "document_number": "3675 9832 4152",
            "full_name": "Aarav Sharma",
            "date_of_birth": "1994-08-15",
            "gender": "MALE",
            "address": "H No 42, Gandhi Road, T Nagar, Chennai, Tamil Nadu - 600017",
            "issuing_authority": "Unique Identification Authority of India",
            "country": "IND",
        },
        "background_color": (255, 252, 245),
        "primary_color": (190, 50, 30),
    },
    "AADHAAR_CARD": {
        "title": "GOVERNMENT OF INDIA - UNIQUE IDENTIFICATION AUTHORITY",
        "fields": {
            "document_number": "3675 9832 4152",
            "full_name": "Aarav Sharma",
            "date_of_birth": "1994-08-15",
            "gender": "MALE",
            "address": "H No 42, Gandhi Road, T Nagar, Chennai, Tamil Nadu - 600017",
            "issuing_authority": "Unique Identification Authority of India",
            "country": "IND",
        },
        "background_color": (255, 252, 245),
        "primary_color": (190, 50, 30),
    },
    "SYNTH_PAN_V1": {
        "title": "INCOME TAX DEPARTMENT - GOVT. OF INDIA",
        "fields": {
            "document_number": "ABCPS1234F",
            "full_name": "AARAV SHARMA",
            "father_name": "RAMESH SHARMA",
            "date_of_birth": "1994-08-15",
            "issuing_authority": "Income Tax Department",
            "country": "IND",
        },
        "background_color": (245, 250, 255),
        "primary_color": (20, 60, 110),
    },
    "PAN_CARD": {
        "title": "INCOME TAX DEPARTMENT - GOVT. OF INDIA",
        "fields": {
            "document_number": "ABCPS1234F",
            "full_name": "AARAV SHARMA",
            "father_name": "RAMESH SHARMA",
            "date_of_birth": "1994-08-15",
            "issuing_authority": "Income Tax Department",
            "country": "IND",
        },
        "background_color": (245, 250, 255),
        "primary_color": (20, 60, 110),
    },
    "SYNTH_UK_DVLA_DL_V1": {
        "title": "DRIVING LICENCE - GREAT BRITAIN (DVLA)",
        "fields": {
            "document_number": "SMITH706254JR9AA01",
            "full_name": "SMITH, JOHN ROBERT",
            "date_of_birth": "1974-06-25",
            "gender": "MALE",
            "issue_date": "2020-07-01",
            "expiry_date": "2030-07-01",
            "address": "10 DOWNING STREET, LONDON, SW1A 2AA",
            "vehicle_classes": "AM, A, B1, B, f, k, p, q",
            "issuing_authority": "DVLA Swansea",
            "country": "GBR",
        },
        "background_color": (255, 248, 252),
        "primary_color": (30, 90, 70),
    },
    "UK_DVLA_DL": {
        "title": "DRIVING LICENCE - GREAT BRITAIN (DVLA)",
        "fields": {
            "document_number": "SMITH706254JR9AA01",
            "full_name": "SMITH, JOHN ROBERT",
            "date_of_birth": "1974-06-25",
            "gender": "MALE",
            "issue_date": "2020-07-01",
            "expiry_date": "2030-07-01",
            "address": "10 DOWNING STREET, LONDON, SW1A 2AA",
            "vehicle_classes": "AM, A, B1, B, f, k, p, q",
            "issuing_authority": "DVLA Swansea",
            "country": "GBR",
        },
        "background_color": (255, 248, 252),
        "primary_color": (30, 90, 70),
    },
}


def generate_synthetic_document_image(
    template_key: str = "SYNTH_NAT_ID_V1",
    format: str = "PNG",
    rotate_degrees: int = 0,
    blur_radius: float = 0.0,
    width: int = 800,
    height: int = 500,
    custom_fields: Optional[Dict[str, str]] = None,
) -> Tuple[bytes, Dict[str, Any], Dict[str, Dict[str, int]]]:
    """Generate a clean synthetic watermarked document image with field bounding boxes."""
    template = SYNTHETIC_TEMPLATES.get(template_key, SYNTHETIC_TEMPLATES["SYNTH_NAT_ID_V1"])
    fields = template["fields"].copy()
    if custom_fields:
        fields.update(custom_fields)

    bg_color = template.get("background_color", (240, 245, 250))
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Outer Border & Header Banner
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=(180, 190, 205), width=3)
    header_color = template.get("primary_color", (30, 60, 120))
    draw.rectangle([(10, 10), (width - 10, 70)], fill=header_color)

    # Header Title
    title = template.get("title", "IDENTITY DOCUMENT")
    draw.text((25, 25), title, fill=(255, 255, 255))
    draw.text((width - 150, 25), "TEST ONLY", fill=(255, 220, 100))

    # 2. Watermark overlay (diagonal across document)
    for y_offset in range(120, height - 80, 70):
        draw.text((30, y_offset), WATERMARK_TEXT, fill=(210, 215, 225))

    # 3. Avatar Placeholder Card
    avatar_box = [(40, 100), (180, 270)]
    draw.rectangle(avatar_box, fill=(215, 225, 240), outline=(160, 175, 200), width=2)
    draw.text((65, 170), "[SYNTH PHOTO]", fill=(120, 140, 170))

    # 4. Render Extracted Fields and compute exact Bounding Boxes
    bounding_boxes: Dict[str, Dict[str, int]] = {}
    y_pos = 100
    x_pos = 210
    line_height = 42

    for key, value in fields.items():
        if y_pos > height - 60:
            break

        label_text = f"{key.replace('_', ' ').upper()}:"
        value_text = str(value)

        # Draw Field
        draw.text((x_pos, y_pos), label_text, fill=(100, 110, 125))
        draw.text((x_pos + 180, y_pos), value_text, fill=(20, 30, 45))

        # Record Bounding Box for provenance tracking
        bounding_boxes[key] = {
            "x_min": x_pos + 180,
            "y_min": y_pos,
            "x_max": x_pos + 180 + len(value_text) * 10,
            "y_max": y_pos + 20,
            "width": len(value_text) * 10,
            "height": 20,
        }
        y_pos += line_height

    # 5. Footer Watermark
    draw.rectangle([(10, height - 40), (width - 10, height - 10)], fill=(230, 235, 245))
    draw.text((20, height - 30), WATERMARK_TEXT, fill=(130, 140, 155))

    # 6. Apply Rotation if requested
    if rotate_degrees:
        img = img.rotate(rotate_degrees, expand=True)

    # 7. Apply Blur if requested
    if blur_radius > 0.0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # 8. Export Bytes
    output = io.BytesIO()
    save_format = format.upper()
    if save_format == "JPG":
        save_format = "JPEG"
    img.save(output, format=save_format)
    image_bytes = output.getvalue()

    return image_bytes, fields, bounding_boxes
