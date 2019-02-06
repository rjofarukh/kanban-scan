import numpy as np
import cv2
import imutils
import json
import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn import svm

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib import colors


###############################################
THRESHOLDS = ""
###############################################

def show_images(*images, scale=4, name="DEFAULT"):
    for image in images:
        height, width = image.shape[:2]
        cv2.namedWindow(name, cv2.WINDOW_NORMAL)

        scale1 = 2560 / width
        scale2 = 1500 / height

        if scale > 0:
            image = cv2.resize(image, None, fx=1/scale, fy=1/scale) 
        elif scale1 <= scale2:
            image = cv2.resize(image, None, fx=1/scale1, fy=1/scale1) 
        else:
            image = cv2.resize(image, None, fx=1/scale2, fy=1/scale2)
    
        cv2.imshow(name, image)

        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
def dilate(image, kern_size = 5, iter_num = 1):
    kernel = np.ones((kern_size, kern_size), np.uint8)
    dilated = cv2.dilate(image, kernel, iterations=iter_num)
    return dilated

def erode(image, kern_size = 5, iter_num = 1):
    kernel = np.ones((kern_size, kern_size), np.uint8)
    eroded = cv2.dilate(image, kernel, iterations=iter_num)
    return eroded

def threshold(image, color):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    min_t, max_t = get_thresh_tuples(color)
    mask = cv2.inRange(hsv_image, min_t, max_t)

    return mask

def threshold_adaptive(image, block_size=5):
    return cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv2.THRESH_BINARY, block_size, 0)

def setup_thresholds(file_name):
    global THRESHOLDS
    if not THRESHOLDS:
        with open(file_name) as infile:
            THRESHOLDS = json.load(infile)

def get_thresh_tuples(color):
    global THRESHOLDS
    if not THRESHOLDS:
        with open(THRESHOLDS_FILE) as infile:
            THRESHOLDS = json.load(infile)

    return (THRESHOLDS[color]["MIN"][0],
            THRESHOLDS[color]["MIN"][1],
            THRESHOLDS[color]["MIN"][2]),(
            THRESHOLDS[color]["MAX"][0],
            THRESHOLDS[color]["MAX"][1],
            THRESHOLDS[color]["MAX"][2])


def plot_hsv(image, root_scale=100):
    image =  cv2.resize(image, None, fx=1.0/root_scale, fy=1.0/root_scale) 
    pixel_colors = image.reshape((np.shape(image)[0]*np.shape(image)[1], 3))

    norm = colors.Normalize(vmin=-1.0,vmax=1.0)
    norm.autoscale(pixel_colors)

    pixel_colors = norm(pixel_colors).tolist()

    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    h,s,v = cv2.split(hsv)

    fig = plt.figure()
    axis = fig.add_subplot(1, 1, 1, projection="3d")
    axis.scatter(h.flatten(), s.flatten(), v.flatten(), facecolors=pixel_colors, marker=".")
    axis.set_xlabel("hue")
    axis.set_ylabel("saturation")
    axis.set_zlabel("value")
    plt.show()

def plot_rgb(image, root_scale=100):
    image =  cv2.resize(image, None, fx=1.0/root_scale, fy=1.0/root_scale) 
    pixel_colors = image.reshape((np.shape(image)[0]*np.shape(image)[1], 3))

    norm = colors.Normalize(vmin=-1.0,vmax=1.0)
    norm.autoscale(pixel_colors)

    pixel_colors = norm(pixel_colors).tolist()

    r,g,b = cv2.split(image)

    fig = plt.figure()
    axis = fig.add_subplot(1, 1, 1, projection="3d")
    axis.scatter(r.flatten(), g.flatten(), b.flatten(), facecolors=pixel_colors, marker=".")
    axis.set_xlabel("red")
    axis.set_ylabel("green")
    axis.set_zlabel("blue")
    plt.show()

def knn_classifier(image_file_dir, root_scale=100, neighbors=6):
    knn = KNeighborsClassifier(n_neighbors=neighbors)
    training, targets = get_training_data(image_file_dir, root_scale=root_scale)
    knn.fit(training, targets)
    return knn

def svm_classifier(image_file_dir, root_scale=100):
    classifier = svm.SVC()
    training, targets = get_training_data(image_file_dir, root_scale=root_scale)
    classifier.fit(training,targets)
    return classifier

def get_training_data(image_file_dir, root_scale=100):
    training = None
    targets = None
    for i in os.listdir(image_file_dir):
        ticket_class = 0
        if i.startswith("TICKET"):
            ticket_class = 255
        print("TRAINING ON " + i)
        image = cv2.imread("../img_training/" + i)
        image =  cv2.resize(image, None, fx=1.0/root_scale, fy=1.0/root_scale) 
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        pixel_colors = hsv.reshape((np.shape(hsv)[0]*np.shape(hsv)[1], 3))
        classes = np.repeat(ticket_class, pixel_colors.shape[0])

        if training is None:
            training = pixel_colors
            targets = classes
        else:
            training = np.append(training, pixel_colors, axis=0)
            targets = np.append(targets, classes)
    
    return training, targets

def prediction(classifier, image, image_name, root_scale=4):

    image =  cv2.resize(image, None, fx=1.0/root_scale, fy=1.0/root_scale) 
    height, width = image.shape[:2]

    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    output = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    data = hsv.reshape((height*width, 3))

    output = np.reshape(classifier.predict(data), (height,width))
    cv2.imwrite(image_name, output)

