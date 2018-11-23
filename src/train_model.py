import cv2
import utils
import imutils

#######################################################
# image = cv2.imread("../img_test/image5.jpg")
# im_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# im_gray = cv2.GaussianBlur(im_gray, (5, 5), 0)

# im_th = cv2.adaptiveThreshold(im_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, 10)
# im_th = cv2.bitwise_not(im_th)
# im_th = utils.dilate(im_th)
# im_th = utils.erode(im_th)
# cv2.imwrite("idk.jpg", im_th)
#######################################################

import cv2
from sklearn.externals import joblib
from skimage.feature import hog
import numpy as np

# Load the classifier
clf = joblib.load("digits_cls.pkl")

im = cv2.imread("../img_test/image5.jpg")
im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
im_gray = cv2.GaussianBlur(im_gray, (5, 5), 0)

im_th = cv2.adaptiveThreshold(im_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, 10)
im_th = cv2.bitwise_not(im_th)
im_th = utils.dilate(im_th)
im_th = utils.erode(im_th)

# Find contours in the image
ctrs = cv2.findContours(im_th.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

ctrs = ctrs[0] if imutils.is_cv2() else ctrs[1]
# Get rectangles contains each contour
rects = [cv2.boundingRect(ctr) for ctr in ctrs]


# For each rectangular region, calculate HOG features and predict
# the digit using Linear SVM.
for rect in rects:
    # Draw the rectangles
    if rect[2] > 5 and rect[3] > 5:
        cv2.rectangle(im, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (0, 255, 0), 3) 
        # Make the rectangular region around the digit
        leng = int(rect[3] * 1.6)
        pt1 = int(rect[1] + rect[3] // 2 - leng // 2)
        pt2 = int(rect[0] + rect[2] // 2 - leng // 2)
        roi = im_th[pt1:pt1+leng, pt2:pt2+leng]

        print(rect)
        # Resize the image
        # WHEN NEAR EDGES - IT BREAKS. FIX?
        roi = cv2.resize(roi, (28, 28), interpolation=cv2.INTER_AREA)
        #roi = cv2.dilate(roi, (3, 3))
        # Calculate the HOG features
        roi_hog_fd = hog(roi, orientations=9, pixels_per_cell=(14, 14), cells_per_block=(1, 1), visualize=False)
        nbr = clf.predict(np.array([roi_hog_fd], 'float64'))
        cv2.putText(im, str(int(nbr[0])), (rect[0], rect[1]),cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)

utils.show_images(im, im_th)