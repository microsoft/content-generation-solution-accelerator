"""
Generate Solution Architecture Diagram for Content Generation Accelerator
Creates a PNG image matching the style of the reference architecture diagram
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Image dimensions
WIDTH = 1400
HEIGHT = 700

# Colors (matching the dark theme)
BG_COLOR = (26, 38, 52)  # #1a2634
BOX_COLOR = (36, 52, 71)  # #243447
BOX_BORDER = (74, 158, 255)  # #4a9eff
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (139, 163, 199)  # #8ba3c7
HIGHLIGHT_BOX = (50, 70, 95)

def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def draw_service_box(draw, x, y, w, h, title, subtitle="", icon_type="default", highlight=False):
    """Draw a service box with icon, title and subtitle"""
    box_fill = HIGHLIGHT_BOX if highlight else BOX_COLOR
    draw_rounded_rect(draw, (x, y, x+w, y+h), radius=8, fill=box_fill, outline=BOX_BORDER, width=1)
    
    # Draw icon placeholder (circle)
    icon_cx = x + w//2
    icon_cy = y + 35
    
    # Different icon styles based on type
    if icon_type == "user":
        draw.ellipse((icon_cx-12, icon_cy-15, icon_cx+12, icon_cy+5), fill=BOX_BORDER)
        draw.ellipse((icon_cx-20, icon_cy+5, icon_cx+20, icon_cy+25), fill=BOX_BORDER)
    elif icon_type == "container":
        draw.rectangle((icon_cx-18, icon_cy-12, icon_cx-4, icon_cy+2), fill=BOX_BORDER)
        draw.rectangle((icon_cx+4, icon_cy-12, icon_cx+18, icon_cy+2), fill=BOX_BORDER)
        draw.rectangle((icon_cx-7, icon_cy+4, icon_cx+7, icon_cy+18), fill=BOX_BORDER)
    elif icon_type == "database":
        draw.ellipse((icon_cx-18, icon_cy-15, icon_cx+18, icon_cy-5), outline=BOX_BORDER, width=2)
        draw.arc((icon_cx-18, icon_cy-5, icon_cx+18, icon_cy+5), 0, 180, fill=BOX_BORDER, width=2)
        draw.line((icon_cx-18, icon_cy-10, icon_cx-18, icon_cy+15), fill=BOX_BORDER, width=2)
        draw.line((icon_cx+18, icon_cy-10, icon_cx+18, icon_cy+15), fill=BOX_BORDER, width=2)
        draw.arc((icon_cx-18, icon_cy+5, icon_cx+18, icon_cy+15), 0, 180, fill=BOX_BORDER, width=2)
    elif icon_type == "ai":
        # Hexagon for AI
        pts = [(icon_cx, icon_cy-18), (icon_cx+16, icon_cy-9), (icon_cx+16, icon_cy+9),
               (icon_cx, icon_cy+18), (icon_cx-16, icon_cy+9), (icon_cx-16, icon_cy-9)]
        draw.polygon(pts, outline=(16, 163, 127), width=2)
        draw.ellipse((icon_cx-6, icon_cy-6, icon_cx+6, icon_cy+6), fill=(16, 163, 127))
    elif icon_type == "webapp":
        draw.rectangle((icon_cx-20, icon_cy-12, icon_cx+20, icon_cy+12), outline=BOX_BORDER, width=2)
        draw.ellipse((icon_cx-15, icon_cy-8, icon_cx-11, icon_cy-4), fill=(255, 95, 87))
        draw.ellipse((icon_cx-9, icon_cy-8, icon_cx-5, icon_cy-4), fill=(254, 188, 46))
        draw.ellipse((icon_cx-3, icon_cy-8, icon_cx+1, icon_cy-4), fill=(40, 200, 64))
    elif icon_type == "storage":
        draw.rectangle((icon_cx-18, icon_cy-12, icon_cx+18, icon_cy+12), outline=BOX_BORDER, width=2)
        draw.line((icon_cx-18, icon_cy-4, icon_cx+18, icon_cy-4), fill=BOX_BORDER, width=1)
        draw.line((icon_cx-10, icon_cy-12, icon_cx-10, icon_cy-4), fill=BOX_BORDER, width=1)
        draw.line((icon_cx, icon_cy-12, icon_cx, icon_cy-4), fill=BOX_BORDER, width=1)
        draw.line((icon_cx+10, icon_cy-12, icon_cx+10, icon_cy-4), fill=BOX_BORDER, width=1)
    else:
        draw.rectangle((icon_cx-18, icon_cy-12, icon_cx+18, icon_cy+12), outline=BOX_BORDER, width=2)
    
    # Draw title
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    
    # Title
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text((x + (w - title_w)//2, y + 60), title, fill=TEXT_WHITE, font=font_title)
    
    # Subtitle (can be multi-line)
    if subtitle:
        lines = subtitle.split('\n')
        y_offset = 78
        for line in lines:
            sub_bbox = draw.textbbox((0, 0), line, font=font_sub)
            sub_w = sub_bbox[2] - sub_bbox[0]
            draw.text((x + (w - sub_w)//2, y + y_offset), line, fill=TEXT_GRAY, font=font_sub)
            y_offset += 14

def draw_arrow(draw, x1, y1, x2, y2):
    """Draw an arrow"""
    draw.line((x1, y1, x2, y2), fill=BOX_BORDER, width=2)
    
    # Arrowhead
    if abs(x2 - x1) > abs(y2 - y1):  # Horizontal
        if x2 > x1:  # Right arrow
            draw.polygon([(x2, y2), (x2-10, y2-5), (x2-10, y2+5)], fill=BOX_BORDER)
        else:  # Left arrow
            draw.polygon([(x2, y2), (x2+10, y2-5), (x2+10, y2+5)], fill=BOX_BORDER)
    else:  # Vertical
        if y2 > y1:  # Down arrow
            draw.polygon([(x2, y2), (x2-5, y2-10), (x2+5, y2-10)], fill=BOX_BORDER)
        else:  # Up arrow
            draw.polygon([(x2, y2), (x2-5, y2+10), (x2+5, y2+10)], fill=BOX_BORDER)

def main():
    # Create image
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Title
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()
    
    draw.text((50, 30), "Content Generation Solution Architecture", fill=TEXT_WHITE, font=font_title)
    
    # Service box dimensions
    BOX_W = 150
    BOX_H = 105
    
    # Layout - Clean left-to-right flow
    # Row 1: Container Registry -> App Service -> Web Frontend
    # Row 2: Container Instance -> Azure OpenAI
    # Row 3: Blob Storage                        Cosmos DB (right side)
    
    ROW1_Y = 100
    ROW2_Y = 290
    ROW3_Y = 480
    
    COL1_X = 100
    COL2_X = 340
    COL3_X = 580
    COL4_X = 820
    COL5_X = 1100
    
    # === ROW 1: Frontend Tier ===
    # Container Registry
    draw_service_box(draw, COL1_X, ROW1_Y, BOX_W, BOX_H, "Container", "Registry", "container")
    
    # App Service
    draw_service_box(draw, COL2_X, ROW1_Y, BOX_W, BOX_H, "App Service", "Node.js Frontend", "webapp")
    
    # Web App (UI)
    draw_service_box(draw, COL4_X, ROW1_Y, BOX_W+50, BOX_H+25, "Web Front-end", "Chat, Generate Content,\nExport Documents", "webapp", highlight=True)
    
    # === ROW 2: Backend Tier ===
    # Container Instance (Backend)
    draw_service_box(draw, COL2_X, ROW2_Y, BOX_W, BOX_H, "Container Instance", "Python/Quart API\nBackend", "container", highlight=True)
    
    # Azure OpenAI Service
    draw_service_box(draw, COL4_X, ROW2_Y, BOX_W+50, BOX_H, "Azure OpenAI", "GPT & DALL-E 3", "ai")
    
    # === ROW 3: Data Storage ===
    # Blob Storage
    draw_service_box(draw, COL2_X, ROW3_Y, BOX_W, BOX_H, "Blob Storage", "Product Images,\nGenerated Content", "storage")
    
    # Cosmos DB
    draw_service_box(draw, COL4_X, ROW3_Y, BOX_W+50, BOX_H, "Cosmos DB", "Briefs, Products,\nChat History", "database")
    
    # === ARROWS (clean flow, no crossings) ===
    
    # Container Registry -> App Service
    draw_arrow(draw, COL1_X+BOX_W, ROW1_Y+BOX_H//2, COL2_X, ROW1_Y+BOX_H//2)
    
    # App Service -> Web Frontend
    draw_arrow(draw, COL2_X+BOX_W, ROW1_Y+BOX_H//2, COL4_X, ROW1_Y+BOX_H//2)
    
    # App Service -> Container Instance (down, API proxy)
    draw_arrow(draw, COL2_X+BOX_W//2, ROW1_Y+BOX_H, COL2_X+BOX_W//2, ROW2_Y)
    
    # Container Registry -> Container Instance (down to pull image)
    draw_arrow(draw, COL1_X+BOX_W//2, ROW1_Y+BOX_H, COL1_X+BOX_W//2, ROW2_Y+BOX_H//2)
    draw_arrow(draw, COL1_X+BOX_W//2, ROW2_Y+BOX_H//2, COL2_X, ROW2_Y+BOX_H//2)
    
    # Container Instance -> Azure OpenAI
    draw_arrow(draw, COL2_X+BOX_W, ROW2_Y+BOX_H//2, COL4_X, ROW2_Y+BOX_H//2)
    
    # Container Instance -> Blob Storage (down)
    draw_arrow(draw, COL2_X+BOX_W//2, ROW2_Y+BOX_H, COL2_X+BOX_W//2, ROW3_Y)
    
    # Container Instance -> Cosmos DB (down-right)
    draw_arrow(draw, COL2_X+BOX_W, ROW2_Y+BOX_H-20, COL4_X, ROW3_Y+BOX_H//2)
    
    # Web Frontend -> Cosmos DB (down)
    draw_arrow(draw, COL4_X+(BOX_W+50)//2, ROW1_Y+BOX_H+25, COL4_X+(BOX_W+50)//2, ROW3_Y)
    
    # === LABELS ===
    draw.text((COL1_X+BOX_W+10, ROW1_Y+BOX_H//2-15), "Pull Image", fill=TEXT_GRAY, font=font_label)
    
    draw.text((COL2_X+BOX_W+60, ROW1_Y+BOX_H//2-15), "HTTPS", fill=TEXT_GRAY, font=font_label)
    
    draw.text((COL2_X+BOX_W//2+8, ROW1_Y+BOX_H+25), "API Proxy", fill=TEXT_GRAY, font=font_label)
    draw.text((COL2_X+BOX_W//2+8, ROW1_Y+BOX_H+37), "(Private VNet)", fill=TEXT_GRAY, font=font_label)
    
    draw.text((COL2_X+BOX_W+60, ROW2_Y+BOX_H//2-15), "Content & Image", fill=TEXT_GRAY, font=font_label)
    draw.text((COL2_X+BOX_W+60, ROW2_Y+BOX_H//2-3), "Generation", fill=TEXT_GRAY, font=font_label)
    
    draw.text((COL2_X+BOX_W//2+8, ROW2_Y+BOX_H+25), "Store/Retrieve", fill=TEXT_GRAY, font=font_label)
    draw.text((COL2_X+BOX_W//2+8, ROW2_Y+BOX_H+37), "Images", fill=TEXT_GRAY, font=font_label)
    
    draw.text((COL2_X+BOX_W+60, ROW2_Y+BOX_H+10), "CRUD", fill=TEXT_GRAY, font=font_label)
    draw.text((COL2_X+BOX_W+60, ROW2_Y+BOX_H+22), "Operations", fill=TEXT_GRAY, font=font_label)
    
    draw.text((COL4_X+(BOX_W+50)//2+8, ROW1_Y+BOX_H+50), "Chat History", fill=TEXT_GRAY, font=font_label)
    
    # Copyright
    try:
        font_copy = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except:
        font_copy = ImageFont.load_default()
    
    draw.text((50, HEIGHT-30), "© 2024 Microsoft Corporation All rights reserved.", fill=TEXT_GRAY, font=font_copy)
    
    # Save image
    output_path = "/home/jahunte/content-generation-solution-accelerator/docs/images/readme/solution_architecture.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Architecture diagram saved to: {output_path}")

if __name__ == "__main__":
    main()
