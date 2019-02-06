import cv2
import utils
import imutils
import h5py

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
from keras.models import load_model
import numpy as np

# Load the classifier
svm = joblib.load("digits_cls.pkl")
cnn = load_model("mnist_keras_cnn_model.h5")

im = cv2.imread("../img_test/image5.jpg")
im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
im_gray = cv2.GaussianBlur(im_gray, (5, 5), 0)

im_th = cv2.adaptiveThreshold(im_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 5, 10)
im_th = cv2.bitwise_not(im_th)

# !! IDEA - overly dialate just to get the areas of interest, then use proper edge detection
# on those regions along with deskewing!!!
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
    x,y,w,h = rect

    if rect[2] > 10 and rect[3] > 10 and rect[2] < 150 and rect[3] < 150:
        cv2.rectangle(im, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (0, 255, 0), 3) 
        # Make the rectangular region around the digit
        leng = int(rect[3] * 1.6)
        pt1 = int(rect[1] + rect[3] // 2 - leng // 2)
        pt2 = int(rect[0] + rect[2] // 2 - leng // 2)


        #will take the cropped rectangle with regular lengths and bitwise OR it with 
        #rectangle of 0s generated with numpy
        #Then in that region will probably use sobel


        #Dimensions will be leng x leng
        # along the x axis, it will be padded with h // 2 + leng // 2
        # along the y axis, it will be padded with w // 2 + leng // 2
    
        # roi = im_th[y:y+h, x:x+w]
        # roi = np.array(roi, 'float32')
        # np.pad(roi, pad_width=((- rect[3] // 2 + leng // 2, -rect[3] // 2 + leng // 2), (-rect[2] // 2 + leng // 2, - rect[2] // 2 + leng // 2)), mode='constant', constant_values=0)
        roi = im_th[pt1:pt1+leng, pt2:pt2+leng]

        # cv2.rectangle(im, (pt2, pt1), (pt2+leng, pt1+leng), (0, 255, 0), 3) 

        #roi = cv2.resize(roi, (28, 28), interpolation=cv2.INTER_AREA)

        print(roi)
        roi = cv2.resize(roi, (28,28))

        # Calculate the HOG features
        #roi_hog_fd = hog(roi, orientations=9, pixels_per_cell=(14, 14), cells_per_block=(1, 1), visualize=False)
        
        #nbr = svm.predict(np.array([roi_hog_fd], 'float64'))
        
        roi_arr = np.array(roi, 'float32') / 255
        roi_arr = roi_arr.reshape(1,28,28,1)

        nbr = cnn.predict(roi_arr).argmax(axis=1)

        cv2.putText(im, str(int(nbr[0])), (rect[0], rect[1]),cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 3)

utils.show_images(im, im_th)