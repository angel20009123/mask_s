"""Render the native geometric network mark at high resolution."""
from pathlib import Path
from PIL import Image, ImageDraw

assets = Path(__file__).parent / "assets"
assets.mkdir(exist_ok=True)
size = 1024
image = Image.new("RGBA", (size, size))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((32, 32, 992, 992), radius=222, fill="#101f3d")
draw.rounded_rectangle((52, 52, 972, 972), radius=202, outline="#304b70", width=5)
# Three subnet layers connected by one shared network spine.
draw.line([(286, 284), (286, 734)], fill="#7194c3", width=30)
colors = ("#70a5ff", "#bc91ff", "#58ddbd")
for y, color in zip((286, 510, 734), colors):
    draw.line([(286, y), (490, y)], fill=color, width=26)
    draw.rounded_rectangle((474, y - 76, 800, y + 76), radius=48, fill=color)
    for x in (544, 624, 704):
        draw.rounded_rectangle((x, y - 24, x + 42, y + 24), radius=10, fill="#152b47")
    draw.ellipse((242, y - 44, 330, y + 44), fill=color)
image.resize((512, 512), Image.Resampling.LANCZOS).save(assets / "mask-studio.png")
image.save(assets / "mask-studio.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("Icon assets created")
