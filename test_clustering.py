#!/usr/bin/env python3
"""Test fixation clustering visualization"""

import numpy as np
import cv2
from heatmap import generate_heatmap, draw_fixation_clusters

# Create synthetic gaze points with clusters
gaze_points = []

# Cluster 1: Top-left region
for _ in range(15):
    x = np.random.normal(200, 30)
    y = np.random.normal(150, 30)
    gaze_points.append((int(x), int(y)))

# Cluster 2: Center region
for _ in range(20):
    x = np.random.normal(600, 40)
    y = np.random.normal(400, 40)
    gaze_points.append((int(x), int(y)))

# Cluster 3: Right region
for _ in range(12):
    x = np.random.normal(1000, 35)
    y = np.random.normal(300, 35)
    gaze_points.append((int(x), int(y)))

print(f"Generated {len(gaze_points)} synthetic gaze points")

# Create a blank image
code_img = 255 * np.ones((600, 1200, 3), dtype=np.uint8)
cv2.putText(code_img, "Test Code Visualization", (400, 100),
           cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)

# Generate heatmap
heat = generate_heatmap(code_img, gaze_points, alpha=0.6)
print("Heatmap generated")

# Add clustering visualization
heat_clustered, cluster_stats = draw_fixation_clusters(heat, gaze_points, eps=50, min_samples=3)
print(f"Clustering complete: {len(cluster_stats)} clusters detected")

# Print cluster statistics
print("\nCluster Statistics:")
for cluster_id, stats in cluster_stats.items():
    cx, cy = stats["centroid"]
    print(f"  Cluster {cluster_id}:")
    print(f"    - Position: ({cx:.0f}, {cy:.0f})")
    print(f"    - Fixations: {stats['fixation_count']}")
    print(f"    - Radius: {stats['radius']} pixels")

# Save result
output_path = "test_clustering_output.png"
cv2.imwrite(output_path, heat_clustered)
print(f"\nVisualization saved to {output_path}")
print("Features shown:")
print("  - Colored circles: Cluster boundaries (radius ~50px)")
print("  - Filled dots: Cluster centroids")
print("  - C#: Cluster labels with fixation counts")
