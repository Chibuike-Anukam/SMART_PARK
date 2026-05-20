import numpy as np
import cv2
import glob
import imutils

image_paths = glob.glob('unstitchedImages3/*.jpg')
images = []


for image in image_paths:
    img = cv2.imread(image)
    images.append(img)
    cv2.imshow('Image', img)
    cv2.waitKey(0)

imageStitcher = cv2.Stitcher_create()

import cv2

# 1. Create the default stitcher object
imageStitcher = cv2.Stitcher_create()

# 2. Adjust the internal scale parameters
# 'registration' is the step that finds features and matches images.
# Lowering this drastically reduces memory usage and speeds up the process.
# Try 0.3 to 0.5 for large images. 
imageStitcher.setRegistrationResol(0.4) 

# 'seam' is the step that finds where to cut and stitch the images together.
# A lower resolution here prevents crashes during the seam-finding process.
imageStitcher.setSeamEstimationResol(0.1)

# 3. Now run the stitching step as normal
error, stitched_img = imageStitcher.stitch(images)


# error, stitched_img = imageStitcher.stitch(images)

if not error:

    cv2.imwrite("stitchedOutput.png", stitched_img)
    cv2.imshow("Stitched Image", stitched_img)
    cv2.waitKey(0)

'''
    stitched_img = cv2.copyMakeBorder(stitched_img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, (0,0,0))

    gray = cv2.cvtColor(stitched_img, cv2.COLOR_BGR2GRAY)
    thresh_img = cv2.threshold(gray, 0, 225, cv2.THRESH_BINARY)[1]

    cv2.imshow("Threshold Image", thresh_img)
    cv2.waitKey(0) # just to see output (can be removed)

    contours = cv2.findContours(thresh_img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    contours = imutils.grab_contours(contours)
    areaOI = max(contours, key=cv2.contourArea)

    mask = np.zeros(thresh_img.shape, dtype="uint8")
    x, y, w, h = cv2.boundingRect(areaOI)
    cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

    minRectangle = mask.copy()
    sub = mask.copy()

    while cv2.countNonZero(sub) > 0: 
        minRectangle = cv2.erode(minRectangle, None)
        sub = cv2.subtract(minRectangle, thresh_img)

    
    contours = cv2.findContours(minRectangle.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    contours = imutils.grab_contours(contours)
    areaOI = max(contours, key=cv2.contourArea)

    cv2.imshow("minRectangle Image", minRectangle)
    cv2.waitKey(0)

    x, y, w, h = cv2.boundingRect(areaOI)

    stitched_img = stitched_img[y:y + h, x:x + w]

    cv2.imwrite("StitchedOutputProcessed.png", stitched_img)

    cv2.imshow("Stitched Image Processed", stitched_img)

    cv2.waitKey(0)


else: 
    print("Images could not be stitched!")
    print("Likely not enough keypoints being detected!")

'''

# --- FAST CROPPING LOGIC to Increase Speed ---
# 1. Add a temporary black border to the original high-res stitched image
stitched_img = cv2.copyMakeBorder(stitched_img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, (0,0,0))

# 2. Create a small copy just for calculating the crop zone
scale_percent = 0.20 # Scale down to 20% of original size
small_w = int(stitched_img.shape[1] * scale_percent)
small_h = int(stitched_img.shape[0] * scale_percent)
small_stitched = cv2.resize(stitched_img, (small_w, small_h))

# 3. Run thresholding on the SMALL image
gray = cv2.cvtColor(small_stitched, cv2.COLOR_BGR2GRAY)
thresh_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)[1]

contours = cv2.findContours(thresh_img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = imutils.grab_contours(contours)
areaOI = max(contours, key=cv2.contourArea)

mask = np.zeros(thresh_img.shape, dtype="uint8")
x, y, w, h = cv2.boundingRect(areaOI)
cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

minRectangle = mask.copy()
sub = mask.copy()

# 4. This loop now runs incredibly fast because the image is small!
while cv2.countNonZero(sub) > 0: 
    minRectangle = cv2.erode(minRectangle, None)
    sub = cv2.subtract(minRectangle, thresh_img)

contours = cv2.findContours(minRectangle.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = imutils.grab_contours(contours)
areaOI = max(contours, key=cv2.contourArea)

# 5. Get the crop coordinates from the SMALL image
x_small, y_small, w_small, h_small = cv2.boundingRect(areaOI)

# 6. SCALE THE COORDINATES BACK UP to match the large original image
x_large = int(x_small / scale_percent)
y_large = int(y_small / scale_percent)
w_large = int(w_small / scale_percent)
h_large = int(h_small / scale_percent)

# 7. Crop the ORIGINAL high-res image
stitched_img_processed = stitched_img[y_large:y_large + h_large, x_large:x_large + w_large]

cv2.imwrite("StitchedOutputProcessed.png", stitched_img_processed)

