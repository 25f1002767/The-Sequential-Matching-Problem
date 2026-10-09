import os
import sys
from pathlib import Path

# Step 1: Render SVGs to PNGs using PySide6
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer

app = QGuiApplication.instance()
if not app:
    app = QGuiApplication(sys.argv)

charts_dir = Path("analysis_output/charts")
svg_files = sorted(list(charts_dir.glob("*.svg")))

print(f"Found {len(svg_files)} SVG files to convert...")
for svg_path in svg_files:
    png_path = svg_path.with_suffix(".png")
    renderer = QSvgRenderer(str(svg_path))
    if renderer.isValid():
        sz = renderer.defaultSize()
        scale = 2.0  # 2x scale for sharp print quality
        w = int(sz.width() * scale)
        h = int(sz.height() * scale)
        img = QImage(w, h, QImage.Format_ARGB32)
        img.fill(QColor("white"))
        painter = QPainter(img)
        renderer.render(painter)
        painter.end()
        img.save(str(png_path))
        print(f"  Rendered: {png_path.name} ({w}x{h})")
    else:
        print(f"  Warning: Invalid SVG {svg_path.name}")

print("All charts rendered to PNG successfully.")
