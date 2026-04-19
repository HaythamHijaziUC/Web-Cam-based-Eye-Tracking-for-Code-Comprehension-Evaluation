import numpy as np
import cv2
from sklearn.cluster import DBSCAN

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

def cluster_gaze_points(gaze_points, eps=50, min_samples=5):
    """
    Cluster gaze points using DBSCAN algorithm.
    
    Args:
        gaze_points: List of (x, y) tuples
        eps: Maximum distance between points in a cluster (pixels)
        min_samples: Minimum points to form a cluster
    
    Returns:
        clusters: Dict with cluster_id -> list of points
        centroids: Dict with cluster_id -> (x, y) centroid
        fixation_counts: Dict with cluster_id -> fixation count
    """
    if len(gaze_points) < min_samples:
        # Single cluster if not enough points
        return {0: gaze_points}, {0: np.mean(gaze_points, axis=0)}, {0: len(gaze_points)}
    
    points_array = np.array(gaze_points, dtype=np.float32)
    
    # DBSCAN clustering
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(points_array)
    labels = clustering.labels_
    
    clusters = {}
    centroids = {}
    fixation_counts = {}
    
    # Group points by cluster
    for idx, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(gaze_points[idx])
    
    # Compute centroids and fixation counts
    for cluster_id, points in clusters.items():
        if cluster_id == -1:  # Noise points
            continue
        centroid = np.mean(points, axis=0)
        centroids[cluster_id] = centroid
        fixation_counts[cluster_id] = len(points)
    
    return clusters, centroids, fixation_counts

def draw_fixation_clusters(heatmap_img, gaze_points, eps=50, min_samples=5):
    """
    Draw fixation clusters and centroids on heatmap with labels.
    
    Args:
        heatmap_img: Heatmap image (BGR)
        gaze_points: List of (x, y) gaze points
        eps: DBSCAN eps parameter (cluster radius)
        min_samples: Minimum points per cluster
    
    Returns:
        annotated_img: Image with cluster overlays
        cluster_stats: Dictionary with cluster statistics
    """
    annotated_img = heatmap_img.copy()
    
    if len(gaze_points) == 0:
        return annotated_img, {}
    
    clusters, centroids, fixation_counts = cluster_gaze_points(gaze_points, eps, min_samples)
    
    # Color palette for clusters
    colors = [
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 0, 255),    # Red
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
        (128, 0, 128),  # Purple
        (255, 165, 0),  # Orange
        (165, 42, 42),  # Brown
        (192, 192, 192) # Gray
    ]
    
    cluster_stats = {}
    cluster_id = 0
    
    for cid, centroid in sorted(centroids.items()):
        color = colors[cluster_id % len(colors)]
        cx, cy = int(centroid[0]), int(centroid[1])
        fixation_count = fixation_counts[cid]
        
        # Draw cluster boundary circle (radius based on eps)
        cv2.circle(annotated_img, (cx, cy), eps, color, 2, cv2.LINE_AA)
        
        # Draw centroid
        cv2.circle(annotated_img, (cx, cy), 5, color, -1)
        
        # Draw fixation count label
        label = f"C{cluster_id}: {fixation_count}"
        cv2.putText(annotated_img, label, (cx + 10, cy - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Store statistics
        cluster_stats[cluster_id] = {
            "centroid": centroid,
            "fixation_count": fixation_count,
            "radius": eps,
            "color": color
        }
        
        cluster_id += 1
    
    return annotated_img, cluster_stats

