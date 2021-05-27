import os
import sys
from .mrcnn.model import MaskRCNN
# from mrcnn.model import log
from .mrcnn.config import Config
import tensorflow as tf
import matplotlib.image as mpimg
import cv2 
from os import path


# Import Mask RCNN
# Root directory of the project
# ROOT_DIR = os.path.abspath("Mask_RCNN")
ROOT_DIR = os.getcwd() 
sys.path.append(ROOT_DIR)  # To find local version of the library
WEIGHT_DIR = os.getcwd() + "/main/mrcnn/weights/"
Weight_PATH = WEIGHT_DIR + "lottery_model.h5"
DEVICE = "/cpu:0"  # /cpu:0 or /gpu:0 
MODEL_DIR = os.path.join(ROOT_DIR, "logs")

class InferenceConfig(Config):
    # Set batch size to 1 since we'll be running inference on
    # one image at a time. Batch size = GPU_COUNT * IMAGES_PER_GPU
    GPU_COUNT = 1
    IMAGES_PER_GPU = 1     
    NAME = "balloon"
    # Number of classes (including background)
    NUM_CLASSES = 3 + 1  # Background + balloon
    # Number of training steps per epoch
    STEPS_PER_EPOCH = 100
    # Skip detections with < 90% confidence
    DETECTION_MIN_CONFIDENCE = 0.9

config = InferenceConfig()

with tf.device(DEVICE):
    model = MaskRCNN(mode="inference", model_dir=MODEL_DIR,
                              config=config)
    # Load weights
    print("Loading weights ", Weight_PATH)
    model.load_weights(Weight_PATH, by_name=True)
    model.keras_model._make_predict_function()


def get_image_parts(image,  outpath = "./output_images"):
    if not os.path.exists(outpath):
        os.mkdir(outpath)
    results1 = model.detect([image], verbose=1)
    r1 = results1[0]
    class_ids = r1['class_ids']
    images_cropped = []
    class_fltr = r1['class_ids'] == class_ids
    boxes = r1['rois'][class_fltr, :]
    for box in boxes:
        y1, x1, y2, x2 = box
        cropped = image[y1: y2, x1: x2]
        images_cropped.append(cropped)

    class_ids_tolist = list(class_ids)
    part_images = []
    temp_image_obj = {}
    for image, class_lst in  zip(images_cropped, class_ids_tolist):
        temp_image_obj['image'] = image
        temp_image_obj['class'] = class_lst
        part_images.append(temp_image_obj)
        cv2.imwrite(path.join(outpath,"dataname_{0}.jpg".format(class_lst)), image)
        print("Saving ", outpath,"dataname_{0}.jpg".format(class_lst))

    return part_images
    
    

