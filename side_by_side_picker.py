import cv2
import numpy as np

img1 = cv2.imread('left.jpg')
img2 = cv2.imread('right.jpg')

# Resize both to the same height for side-by-side display
DISPLAY_H = 800
scale1 = DISPLAY_H / img1.shape[0]
scale2 = DISPLAY_H / img2.shape[0]

d1 = cv2.resize(img1, (int(img1.shape[1] * scale1), DISPLAY_H))
d2 = cv2.resize(img2, (int(img2.shape[1] * scale2), DISPLAY_H))

# Stick them side by side
combined = np.hstack([d1, d2])
offset = d1.shape[1]  # x offset where photo2 starts

pts1 = []  # points in photo1
pts2 = []  # points in photo2
current = []  # buffer for the current pair

COLORS = [
    (0, 255, 0), (0, 0, 255), (255, 0, 0),
    (0, 255, 255), (255, 0, 255), (255, 165, 0)
]

def click(event, x, y, flags, param):
    if event != cv2.EVENT_LBUTTONDOWN:
        return

    color = COLORS[len(pts1) % len(COLORS)]

    if x < offset:
        # Clicked on photo1 side
        if len(pts1) == len(pts2):  # photo1 goes first for each pair
            real_x = int(x / scale1)
            real_y = int(y / scale1)
            pts1.append((real_x, real_y))
            cv2.circle(combined, (x, y), 8, color, -1)
            cv2.putText(combined, str(len(pts1)), (x + 10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            print(f"Marker {len(pts1)} in Photo1: ({real_x}, {real_y}) — now click the same point in Photo2")
        else:
            print("Click the matching point in Photo2 first!")
    else:
        # Clicked on photo2 side
        if len(pts2) < len(pts1):  # photo2 goes second for each pair
            real_x = int((x - offset) / scale2)
            real_y = int(y / scale2)
            pts2.append((real_x, real_y))
            cv2.circle(combined, (x, y), 8, color, -1)
            cv2.putText(combined, str(len(pts2)), (x + 10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            print(f"Marker {len(pts2)} in Photo2: ({real_x}, {real_y}) — click next point in Photo1")

            # Draw a line connecting the pair
            p1_display = (int(pts1[-1][0] * scale1), int(pts1[-1][1] * scale1))
            p2_display = (int(pts2[-1][0] * scale2) + offset, int(pts2[-1][1] * scale2))
            cv2.line(combined, p1_display, p2_display, color, 1)
        else:
            print("Click the matching point in Photo1 first!")

    cv2.imshow('Click matching pairs — LEFT then RIGHT', combined)

cv2.imshow('Click matching pairs — LEFT then RIGHT', combined)
cv2.setMouseCallback('Click matching pairs — LEFT then RIGHT', click)

print("Instructions:")
print("  1. Click a shared marker in the LEFT image")
print("  2. Click the same marker in the RIGHT image")
print("  3. Repeat for all shared markers (minimum 4)")
print("  Press S to save points and continue, Q to quit\n")

while True:
    key = cv2.waitKey(0) & 0xFF
    if key == ord('q'):
        break
    if key == ord('s'):
        if len(pts1) < 4:
            print(f"Need at least 4 pairs, you have {len(pts1)}. Keep clicking.")
        else:
            print(f"\nSaved {len(pts1)} point pairs.")
            break

cv2.destroyAllWindows()

# Save points to a file so you don't have to redo this
np.save('pts1.npy', np.float32(pts1))
np.save('pts2.npy', np.float32(pts2))

print("pts1 =", pts1)
print("pts2 =", pts2)