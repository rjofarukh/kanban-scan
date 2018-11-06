import numpy as np
import cv2
import imutils

def show_images(*images, scale=4, name="DEFAULT"):

    for image in images:
        height, width = image.shape[:2]
        cv2.namedWindow(name, cv2.WINDOW_NORMAL)

        image = cv2.resize(image, None, fx=1/scale, fy=1/scale) 
        cv2.imshow(name, image)

        cv2.waitKey(0)
        cv2.destroyAllWindows()
    