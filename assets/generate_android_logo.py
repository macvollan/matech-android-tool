"""
MacTech Android Tool - Precision Vector-Style Icon & Logo Generator
Creates ultra-crisp Android forensic shield & bugdroid icons in multiple resolutions.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_android_icon(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    
    # Render at 4x resolution (2048x2048) and downsample with Lanczos for super-smooth antialiasing
    size = 2048
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2

    # 1. Outer Hexagonal / Shield Cyber Base
    # Deep gradient background container
    bg_pad = 120
    radius = 380
    
    # Outer glowing ring / rounded squircle
    draw.rounded_rectangle(
        [bg_pad, bg_pad, size - bg_pad, size - bg_pad],
        radius=radius,
        fill=(11, 15, 23, 255),
        outline=(37, 99, 235, 255), # MacTech Cobalt Blue
        width=28
    )

    # Inner subtle glow border
    draw.rounded_rectangle(
        [bg_pad + 24, bg_pad + 24, size - bg_pad - 24, size - bg_pad - 24],
        radius=radius - 20,
        fill=None,
        outline=(56, 189, 248, 120), # Cyan glow
        width=10
    )

    # Circuit traces in the background
    trace_color = (30, 41, 59, 180)
    for offset in [-600, -300, 0, 300, 600]:
        draw.line([(bg_pad + 80, cy + offset), (size - bg_pad - 80, cy + offset)], fill=trace_color, width=8)

    # 2. Android Bugdroid Dome (Official Android Silhouette with Cyber Touch)
    # Head Dome Center
    head_cx = cx
    head_cy = cy - 40
    head_w = 1100
    head_h = 900
    
    # Draw Head Dome Arc (Semi-circle)
    # Bounding box for the top dome:
    dome_box = [head_cx - head_w // 2, head_cy - head_h // 2, head_cx + head_w // 2, head_cy + head_h // 2]
    
    # Android Green: (61, 220, 132) #3DDC84
    android_green = (61, 220, 132, 255)
    android_dark_green = (16, 185, 129, 255)
    cyber_cyan = (56, 189, 248, 255)
    
    # Head semicircle
    draw.pieslice(dome_box, start=180, end=360, fill=android_green)

    # Antennae
    # Left antenna
    ant_len = 240
    ant_w = 48
    draw.line([(head_cx - 260, head_cy - 380), (head_cx - 400, head_cy - 380 - ant_len)], fill=android_green, width=ant_w)
    # Antenna tips (rounded)
    draw.ellipse([head_cx - 400 - ant_w // 2, head_cy - 380 - ant_len - ant_w // 2, head_cx - 400 + ant_w // 2, head_cy - 380 - ant_len + ant_w // 2], fill=android_green)
    
    # Right antenna
    draw.line([(head_cx + 260, head_cy - 380), (head_cx + 400, head_cy - 380 - ant_len)], fill=android_green, width=ant_w)
    draw.ellipse([head_cx + 400 - ant_w // 2, head_cy - 380 - ant_len - ant_w // 2, head_cx + 400 + ant_w // 2, head_cy - 380 - ant_len + ant_w // 2], fill=android_green)

    # Eyes: High-Tech Cyber Visor or Dual Glowing Sensors
    eye_y = head_cy - 160
    eye_r = 75
    # Left eye
    draw.ellipse([head_cx - 240 - eye_r, eye_y - eye_r, head_cx - 240 + eye_r, eye_y + eye_r], fill=(11, 15, 23, 255))
    draw.ellipse([head_cx - 240 - eye_r // 2, eye_y - eye_r // 2, head_cx - 240 + eye_r // 2, eye_y + eye_r // 2], fill=cyber_cyan)
    # Right eye
    draw.ellipse([head_cx + 240 - eye_r, eye_y - eye_r, head_cx + 240 + eye_r, eye_y + eye_r], fill=(11, 15, 23, 255))
    draw.ellipse([head_cx + 240 - eye_r // 2, eye_y - eye_r // 2, head_cx + 240 + eye_r // 2, eye_y + eye_r // 2], fill=cyber_cyan)

    # 3. Forensic Diagnostic Shield / Crosshair Element at the bottom
    shield_top = head_cy + 40
    shield_box = [cx - 420, shield_top, cx + 420, shield_top + 540]
    
    # Shield shape points
    shield_points = [
        (cx - 360, shield_top),
        (cx + 360, shield_top),
        (cx + 360, shield_top + 240),
        (cx, shield_top + 520),
        (cx - 360, shield_top + 240)
    ]
    draw.polygon(shield_points, fill=(19, 26, 41, 240), outline=(56, 189, 248, 255))
    # Border line for shield
    draw.line(shield_points + [shield_points[0]], fill=(56, 189, 248, 255), width=24)

    # High-tech wrench & lightning bolt / ADB pulse inside shield
    bolt_points = [
        (cx + 20, shield_top + 80),
        (cx - 100, shield_top + 260),
        (cx - 10, shield_top + 260),
        (cx - 40, shield_top + 420),
        (cx + 100, shield_top + 220),
        (cx + 10, shield_top + 220),
    ]
    draw.polygon(bolt_points, fill=android_green)

    # Downsample to 512x512
    icon_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    icon_512_path = os.path.join(output_dir, "icon.png")
    icon_512.save(icon_512_path, "PNG")
    print(f"✔ Saved: {icon_512_path}")

    # Generate multi-res Windows ICO file
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    ico_path = os.path.join(output_dir, "icon.ico")
    icon_512.save(ico_path, format="ICO", sizes=icon_sizes)
    print(f"✔ Saved: {ico_path}")

    # 4. Generate Wide Banner Logo (1200x400)
    banner_w, banner_h = 1200, 400
    banner = Image.new("RGBA", (banner_w, banner_h), (11, 15, 23, 255))
    b_draw = ImageDraw.Draw(banner)
    
    # Paste icon resized to 300x300 on the left
    icon_300 = icon_512.resize((300, 300), Image.Resampling.LANCZOS)
    banner.paste(icon_300, (50, 50), icon_300)

    # Add Text on right
    # Title
    try:
        font_large = ImageFont.truetype("arialbd.ttf", 64)
        font_sub = ImageFont.truetype("arial.ttf", 28)
        font_pill = ImageFont.truetype("arialbd.ttf", 22)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_pill = ImageFont.load_default()

    b_draw.text((400, 80), "MacTech Android Tool", fill=(248, 250, 252, 255), font=font_large)
    b_draw.text((400, 165), "Enterprise Mobile Forensics, Diagnostics & ADB Suite", fill=(56, 189, 248, 255), font=font_sub)
    b_draw.text((400, 215), "Authenticity Kernel Inspector • 0% Terminal Flashing • TRIM Defrag", fill=(148, 163, 184, 255), font=font_sub)

    # Pill badge
    b_draw.rounded_rectangle([400, 280, 680, 325], radius=8, fill=(16, 185, 129, 40), outline=(16, 185, 129, 255), width=2)
    b_draw.text((420, 290), "★ OFFICIAL RELEASE v2.2", fill=(61, 220, 132, 255), font=font_pill)

    banner_path = os.path.join(output_dir, "logo.png")
    banner.save(banner_path, "PNG")
    print(f"✔ Saved: {banner_path}")

if __name__ == "__main__":
    assets_dir = os.path.dirname(os.path.abspath(__file__))
    create_android_icon(assets_dir)
