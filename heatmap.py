import numpy as np
import cv2

def generate_heatmap(code_img, gaze_points, alpha=0.5):
    h, w = code_img.shape[:2]
    heat = np.zeros((h, w), dtype=np.float32)

    for x, y in gaze_points:
        if 0 <= x < w and 0 <= y < h:
            heat[y, x] += 1

    heat = cv2.GaussianBlur(heat, (51, 51), 0)
    heat_norm = cv2.normalize(heat, None, 0, 255, cv2.NORM_MINMAX)
    heat_color = cv2.applyColorMap(heat_norm.astype(np.uint8), cv2.COLORMAP_JET)

    blended = cv2.addWeighted(code_img, 1 - alpha, heat_color, alpha, 0)
    return blended
