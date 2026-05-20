import cv2
import numpy as np

# ── 1. LOAD IMAGES ────────────────────────────────────────────────
img1 = cv2.imread('left.jpg')
img2 = cv2.imread('right.jpg')

# ── 2. PASTE YOUR CLICKED POINTS HERE ─────────────────────────────
# These are the same physical markers clicked in the same order
# in both photos. You need at least 4 shared markers.

# Points clicked in left (original resolution)
pts1 = np.float32([
    [6210, 640],   # marker 1
    [3790, 3290],   # marker 2
    [8600, 3320],  # marker 3
    [6050, 5590],  # marker 4
])

# The same physical markers clicked in right
pts2 = np.float32([
    [3340,  770],   # marker 1
    [850, 3430],   # marker 2
    [5670, 3510],  # marker 3
    [3110, 5810],  # marker 4
])

# ── 3. DEFINE WHERE THOSE POINTS SHOULD GO IN THE FINAL TOP-DOWN VIEW
# This is your "ideal" flat coordinate space.
# Think of this as defining what the surface looks like from directly above.
# Measure the real-world distances between your markers if you can,
# otherwise estimate based on their relative positions.

OUTPUT_W = 1200  # width of final stitched image in pixels --- CHANGE BASED ON YOUR MEASUREMENTS
OUTPUT_H = 800   # height of final stitched image in pixels --- CHANGE BASED ON YOUR MEASUREMENTS

# Where each marker should land in the output (top-down view)
# Adjust these to match the real layout of your markers on the surface
pts_dst = np.float32([
    [100,  100],   # marker 1 → top-left area
    [700,  100],   # marker 2 → top-right area
    [100,  700],   # marker 3 → bottom-left area
    [700,  700],   # marker 4 → bottom-right area
])

######## SEE WHAT CLAUDE DID


# ── 4. COMPUTE HOMOGRAPHIES ────────────────────────────────────────
# Each photo gets its own homography into the shared top-down space
H1, _ = cv2.findHomography(pts1, pts_dst, cv2.RANSAC)
H2, _ = cv2.findHomography(pts2, pts_dst, cv2.RANSAC)

# ── 5. WARP BOTH IMAGES INTO TOP-DOWN VIEW ─────────────────────────
warped1 = cv2.warpPerspective(img1, H1, (OUTPUT_W, OUTPUT_H))
warped2 = cv2.warpPerspective(img2, H2, (OUTPUT_W, OUTPUT_H))

# ── 6. BLEND THE TWO WARPED IMAGES ────────────────────────────────
# Create masks — pixels that are non-black in each warped image
mask1 = (cv2.cvtColor(warped1, cv2.COLOR_BGR2GRAY) > 0).astype(np.float32)
mask2 = (cv2.cvtColor(warped2, cv2.COLOR_BGR2GRAY) > 0).astype(np.float32)

# Where both images overlap, average them
# Where only one image covers, use that image
overlap = (mask1 > 0) & (mask2 > 0)
only1   = (mask1 > 0) & (mask2 == 0)
only2   = (mask2 > 0) & (mask1 == 0)

result = np.zeros_like(warped1, dtype=np.float32)

for c in range(3):  # for each colour channel
    result[:, :, c][overlap] = (
        warped1[:, :, c][overlap].astype(np.float32) * 0.5 +
        warped2[:, :, c][overlap].astype(np.float32) * 0.5
    )
    result[:, :, c][only1] = warped1[:, :, c][only1]
    result[:, :, c][only2] = warped2[:, :, c][only2]

result = result.astype(np.uint8)

# ── 7. SAVE AND SHOW ───────────────────────────────────────────────
cv2.imwrite('stitched_topdown.png', result)

# Show each step so you can debug
cv2.imshow('Photo 1 warped', cv2.resize(warped1, (800, 500)))
cv2.imshow('Photo 2 warped', cv2.resize(warped2, (800, 500)))
cv2.imshow('Final stitched', cv2.resize(result, (800, 500)))
cv2.waitKey(0)
cv2.destroyAllWindows()

print("Saved to stitched_topdown.png")