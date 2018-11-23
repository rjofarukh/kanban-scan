# Import the modules
from sklearn.externals import joblib
from sklearn import datasets
from skimage.feature import hog
from sklearn.svm import LinearSVC
import numpy as np
from collections import Counter
from keras.datasets import mnist


(data_train, target_train), (x_test, y_test) = mnist.load_data()
data_train = data_train.reshape(data_train.shape[0], 28, 28, 1)


print(data_train[0])
# Load the dataset

# Extract the features and labels
features = np.array(data_train, 'int16') 
labels = np.array(target_train, 'int')

# Extract the hog features
list_hog_fd = []
for feature in features:
    fd = hog(feature.reshape((28, 28)), orientations=9, pixels_per_cell=(14, 14), cells_per_block=(1, 1), visualize=False)
    list_hog_fd.append(fd)
hog_features = np.array(list_hog_fd, 'float64')


# Create an linear SVM object
clf = LinearSVC()

# Perform the training
clf.fit(hog_features, labels)

# Save the classifier
joblib.dump(clf, "digits_cls.pkl", compress=3)