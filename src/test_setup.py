import cv2
import tensorflow as tf
from mtcnn import MTCNN
from keras_facenet import FaceNet

print("OpenCV Version :", cv2.__version__)
print("TensorFlow Version :", tf.__version__)

detector = MTCNN()
embedder = FaceNet()

print("Everything Installed Successfully!")