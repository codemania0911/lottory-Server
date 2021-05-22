# Food Menu digitalization by using Mask R-CNN and NLP

This is  Django web application that supports food menu digitalization. 
The repository includes:
* Source code of django web server
* Pre-trained weights for Mask R-CNN and NLP of Food Menu

## Requirements
Python 3.x, TensorFlow 1.14.0, Keras 2.2.5 and other common packages listed in `requirements.txt`.

After install NLTK, you have to run this code before run this django.

  ```python3
    import nltk
    nltk.download('punkt')
    nltk.download('all')
  ```
(Optional) If server can't process threading, you can run this:
  ```bash
    sudo python3 manage.py runserver 0.0.0.0:8000  --nothreading --noreload
  ```


## Installation
1. Clone this repository
2. Install dependencies
   ```bash
   pip3 install -r requirements.txt
   ```
3. Download pre-trained Mask R-CNN weights (fiverr_menu.h5) from the [page](https://drive.google.com/u/0/uc?id=1kx4h8SraYfcAzumiyjntjLZzZpNlO8vp). and locate it to /main/mrcnn/weiths/

## For training
Take a look the [Doc](Samples/guide.docm) for the workflow from scratch including Labeling and Training.

## Getting Started for testing code
* [demo.ipynb](Samples/menu_ocr2_20210510.ipynb) Is the easiest way to start. It shows an example of using a model pre-trained on Food menu to segment objects in your own images.
It includes code to run object detection and instance segmentation on arbitrary images.