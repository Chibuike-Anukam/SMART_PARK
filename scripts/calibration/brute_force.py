import cv2
import numpy as np

img1 = cv2.imread('left.jpg')
img2 = cv2.imread('right.jpg')

# Points clicked in left (original resolution)
pts1 = np.float32([
    [1570, 820],   # marker 1
    [1000, 2000],   # marker 2
    [2330, 1930],  # marker 3
    [1540, 2920],  # marker 4
])

# The same physical markers clicked in right
pts2 = np.float32([
    [880,  830],   # marker 1
    [320, 2010],   # marker 2
    [1630, 1920],  # marker 3
    [850, 2930],  # marker 4
])

# ── OPTION: derive output size from photo1's dimensions ───────────
# Use photo1's actual pixel positions as the destination
# This means "make photo1 look like it does now, warp photo2 to match"
# Only works well if photo1 is already fairly close to top-down

OUTPUT_W = 1400
OUTPUT_H = 1900
PADDING  = 0

# Normalize pts1 to fit nicely in the output canvas
# Find bounding box of pts1
x_coords = pts1[:, 0]
y_coords = pts1[:, 1]
x_min, x_max = x_coords.min(), x_coords.max()
y_min, y_max = y_coords.min(), y_coords.max()

# Scale pts1 to fill the output canvas with padding
def normalize_pts(pts, x_min, x_max, y_min, y_max, out_w, out_h, pad):
    pts_out = pts.copy()
    pts_out[:, 0] = (pts[:, 0] - x_min) / (x_max - x_min) * (out_w - 2*pad) + pad
    pts_out[:, 1] = (pts[:, 1] - y_min) / (y_max - y_min) * (out_h - 2*pad) + pad
    return pts_out

pts_dst = normalize_pts(pts1, x_min, x_max, y_min, y_max, OUTPUT_W, OUTPUT_H, PADDING)

# Now compute homographies using these derived destinations
H1, _ = cv2.findHomography(pts1, pts_dst, cv2.RANSAC)
H2, _ = cv2.findHomography(pts2, pts_dst, cv2.RANSAC)

warped1 = cv2.warpPerspective(img1, H1, (OUTPUT_W, OUTPUT_H))
warped2 = cv2.warpPerspective(img2, H2, (OUTPUT_W, OUTPUT_H))

# ── BLEND ─────────────────────────────────────────────────────────
mask1 = (cv2.cvtColor(warped1, cv2.COLOR_BGR2GRAY) > 0).astype(np.float32)
mask2 = (cv2.cvtColor(warped2, cv2.COLOR_BGR2GRAY) > 0).astype(np.float32)

overlap = (mask1 > 0) & (mask2 > 0)
only1   = (mask1 > 0) & (mask2 == 0)
only2   = (mask2 > 0) & (mask1 == 0)

result = np.zeros_like(warped1, dtype=np.float32)
for c in range(3):
    result[:, :, c][overlap] = (
        warped1[:, :, c][overlap] * 0.5 +
        warped2[:, :, c][overlap] * 0.5
    )
    result[:, :, c][only1] = warped1[:, :, c][only1]
    result[:, :, c][only2] = warped2[:, :, c][only2]

result = result.astype(np.uint8)

cv2.imwrite('stitched_topdown.png', result)
cv2.imshow('Warped 1',  cv2.resize(warped1, (800, 500)))
cv2.imshow('Warped 2',  cv2.resize(warped2, (800, 500)))
cv2.imshow('Stitched',  cv2.resize(result,  (800, 500)))
cv2.waitKey(0)
cv2.destroyAllWindows()