import cv2

# Change this to 'photo1.jpg' or 'photo2.jpg'
IMAGE_PATH = 'left.jpg'

points = []
img = cv2.imread(IMAGE_PATH)

# Resize for display if image is very large (phone photos are huge)
display_scale = 0.1
display = cv2.resize(img, (
    int(img.shape[1] * display_scale),
    int(img.shape[0] * display_scale)
))

def click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((
            int(x / display_scale),  # scale back to original resolution
            int(y / display_scale)
        ))
        # Draw a circle on the display image so you can see what you clicked
        cv2.circle(display, (x, y), 8, (0, 255, 0), -1)
        cv2.putText(display, str(len(points)), (x + 10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow('Pick Markers', display)
        print(f"Point {len(points)}: ({points[-1][0]}, {points[-1][1]})")

cv2.imshow('Pick Markers', display)
cv2.setMouseCallback('Pick Markers', click)
print("Click your markers IN ORDER. Press Q when done.")
cv2.waitKey(0)
cv2.destroyAllWindows()

print("\nCopy these into your stitch script:")
print(f"pts_photo1 = {points}")  # change label depending on which photo