import cv2
import numpy as np

def load_code_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()

def render_code(lines, width=1200, line_height=30):
    height = line_height * len(lines) + 40
    img = 255 * np.ones((height, width, 3), dtype=np.uint8)

    line_regions = []
    y = 40

    for i, line in enumerate(lines):
        cv2.putText(
            img,
            f"{i+1:03d}  {line.rstrip()}",
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            1,
            cv2.LINE_AA
        )
        line_regions.append((y - line_height + 5, y + 5))
        y += line_height

    return img, line_regions
