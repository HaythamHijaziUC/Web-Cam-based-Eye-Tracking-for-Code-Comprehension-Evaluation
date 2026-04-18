import cv2
import numpy as np
import time
from sklearn.linear_model import LinearRegression
import pickle

CALIB_POINTS = [
    (0.5, 0.5),
    (0.1, 0.1),
    (0.9, 0.1),
    (0.1, 0.9),
    (0.9, 0.9)
]

def show_point(screen_w, screen_h, px, py):
    win = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)
    cv2.circle(win, (int(px), int(py)), 20, (0,255,0), -1)
    cv2.imshow("Calibration", win)
    cv2.waitKey(1)

def collect_samples(get_gaze_features, screen_w, screen_h):
    X = []
    Y = []

    for nx, ny in CALIB_POINTS:
        sx = int(nx * screen_w)
        sy = int(ny * screen_h)

        print(f"\nLook at point ({sx}, {sy}) and press SPACE")
        while True:
            show_point(screen_w, screen_h, sx, sy)
            if cv2.waitKey(1) == 32:
                break

        for _ in range(20):
            feats = get_gaze_features()
            if feats is not None:
                X.append(feats)
                Y.append([sx, sy])
            time.sleep(0.02)

    cv2.destroyWindow("Calibration")
    return np.array(X), np.array(Y)

def train_model(X, Y):
    model = LinearRegression()
    model.fit(X, Y)
    return model

def save_model(model, path="calibration_model.pkl"):
    with open(path, "wb") as f:
        pickle.dump(model, f)

def load_model(path="calibration_model.pkl"):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except:
        return None
