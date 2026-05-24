import cv2
import numpy as np

# ── 1. LOAD IMAGES ────────────────────────────────────────────────
img1 = cv2.imread('left.jpg')
img2 = cv2.imread('right.jpg')

# ── 2. PASTE YOUR CLICKED POINTS HERE ─────────────────────────────
# These are the same physical markers clicked in the same order
# in both photos. You need at least 4 shared markers.

# Points clicked in left (original resolution)
'''
pts1 = np.float32([
    [1570, 820],   # marker 1
    [1000, 2000],   # marker 2
    [2330, 1930],  # marker 3
    [1540, 2920],  # marker 4
])'''
pts1 = np.float32([(1572, 838), (979, 2022), (2321, 1975), (1561, 2908)])

# The same physical markers clicked in right
'''
pts2 = np.float32([
    [880,  830],   # marker 1
    [320, 2010],   # marker 2
    [1630, 1920],  # marker 3
    [850, 2930],  # marker 4
])'''
pts2 = np.float32([(896, 827), (303, 2027), (1629, 1970), (875, 2934)])

# ── 3. DEFINE WHERE THOSE POINTS SHOULD GO IN THE FINAL TOP-DOWN VIEW
# This is your "ideal" flat coordinate space.
# Think of this as defining what the surface looks like from directly above.
# Measure the real-world distances between your markers if you can,
# otherwise estimate based on their relative positions.

# scale: 1cm = 10px

OUTPUT_W = 1800  # width of final stitched image in pixels --- CHANGE BASED ON YOUR MEASUREMENTS
OUTPUT_H = 2400   # height of final stitched image in pixels --- CHANGE BASED ON YOUR MEASUREMENTS

# Where each marker should land in the output (top-down view)
# Adjust these to match the real layout of your markers on the surface
pts_dst = np.float32([
    [700,  600],   # marker 1 - 7cm right, 6cm down     ### CHANGE LOCATION OF ONE POINT AT A TIME AND SEE RESULT
    [400,  1100],   # marker 2 - 4cm right, 11cm down   ## TRY RETAKING PHOTOS, BUT USE TINY STICKERS OR SOMETHING SMALL SO YOU DON'T HAVE TO WORRY ABOUT MEASURING TO THE CENTRE OF THE MARKER
    [1000,  1100],   # marker 3 - 10cm right, 11cm down
    [700,  1500],   # marker 4 - 7cm right, 15cm down
])

''' Original output points
pts_dst = np.float32([
    [700,  600],   # marker 1 - 7cm right, 6cm down 
    [400,  1100],   # marker 2 - 4cm right, 11cm down
    [1000,  1100],   # marker 3 - 10cm right, 11cm down
    [700,  1500],   # marker 4 - 7cm right, 15cm down
])'''



# ── 4. COMPUTE HOMOGRAPHIES ────────────────────────────────────────
# Each photo gets its own homography into the shared top-down space
H1, _ = cv2.findHomography(pts1, pts_dst, cv2.RANSAC)
H2, _ = cv2.findHomography(pts2, pts_dst, cv2.RANSAC)

# ── 5. WARP BOTH IMAGES INTO TOP-DOWN VIEW ─────────────────────────   ## ASK CLAUDE WHY WE DID THIS IF BOTH IMAGES ARE ALREADY TOP-DOWN
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
cv2.imshow('Left image warped', cv2.resize(warped1, (800, 500)))
#cv2.imwrite('left_warped.png', warped1)
cv2.imshow('Right image warped', cv2.resize(warped2, (800, 500)))
#cv2.imwrite('right_warped.png', warped2)
cv2.imshow('Final stitched', cv2.resize(result, (800, 500)))
cv2.waitKey(0)
cv2.destroyAllWindows()

print("Saved to stitched_topdown.png")