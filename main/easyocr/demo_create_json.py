import json
import os
import cv2    
import mmcv
from main.easyocr.mmdet.apis import (inference_detector,
                        init_detector, show_result_pyplot)
import matplotlib.pyplot as plt
from PIL import Image
import glob
import re
import numpy as np
import easyocr

# The file path of config file ocr.py and latest.pth
config_file = "/home/ubuntu/lotto/main/easyocr/weights/ocr.py"
checkpoint_file = '/home/ubuntu/lotto/main/easyocr/weights/latest.pth'
model = init_detector(config_file, checkpoint_file, device='cpu')
imgs = glob.glob(r'/home/ubuntu/lotto/output_images/*.jpg')


def resize_img(img):
    w = 1333
    r = img.shape[1] / w
    h = int(img.shape[0] / r)
    new_img = cv2.resize(img,(w,h))
    return new_img

def split_img(img, show = False):
    img = resize_img(img)
    img_r = img[:,:,-1]
    ret3,th3 = cv2.threshold(img_r,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)    
    kernel = np.ones((1,21), np.uint8)
    img_dilation = cv2.erode(th3, kernel, iterations=21)
    img_bitwise = cv2.bitwise_not(img_dilation)    
    contours,_ = cv2.findContours(img_bitwise, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    bboxes1 = []
    _ = img.copy()
    pad = 15
    for i,c in enumerate(contours):
        x,y,w,h = cv2.boundingRect(c)
        if w > 1000:
            bboxes1.append([x,max(0,y-pad),x+w,min(img.shape[0],y+h+pad)])
            cv2.rectangle(_,(x,y),(x+w,y+h),(0,0,255),3)    
    def _sort_ymin(el):
        return el[1]
    bboxes1.sort(key=_sort_ymin)
    list_img = []
    for i in bboxes1:
        x0,y0,x1,y1 = i
        _img = img[y0:y1,x0:x1]
        list_img.append(_img)
    return list_img,bboxes1
def non_max_suppression_fast(flat_x, overlapThresh):
	# if there are no flat_x, return an empty list
    if len(flat_x) == 0:
        return []
	# initialize the list of picked indexes	
    pick = []
	# grab the coordinates of the bounding flat_x
    x1 = np.array([_[0] for _ in flat_x])
    y1 = np.array([_[1] for _ in flat_x])
    x2 = np.array([_[2] for _ in flat_x])
    y2 = np.array([_[3] for _ in flat_x])
	# compute the area of the bounding flat_x and sort the bounding
	# flat_x by the bottom-right y-coordinate of the bounding box
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(y2)
	# keep looping while some indexes still remain in the indexes
	# list
    while len(idxs) > 0:
        # grab the last index in the indexes list and add the
        # index value to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)
        # find the largest (x, y) coordinates for the start of
        # the bounding box and the smallest (x, y) coordinates
        # for the end of the bounding box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])
        # compute the width and height of the bounding box
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)
        # compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]
        # delete all indexes from the index list that have
        idxs = np.delete(idxs, np.concatenate(([last],
            np.where(overlap > overlapThresh)[0])))
    # return only the bounding flat_x that were picked using the
    # integer data type
    final = [flat_x[_] for _ in pick]
    return final
    
# x = result[2]
def print_line(r,thr):
    '''
    x is the result of one image
    '''
    # add this line, it doesnot change the origin result
    # ------------------------
    x = r.copy()
    # ------------------------
    # take value > 0.6
    for i,_x in enumerate(x):
        x[i] = [_ for _ in _x if _[-1] > thr]

    for i,_x in enumerate(x):
        for j,__x in enumerate(_x):
            x[i][j] = np.append(x[i][j],i)

    flat_x = []
    for i in range(len(x)):
        for j in range(len(x[i])):
            flat_x.append(x[i][j])
    # should tune this 0.5
    flat_x = non_max_suppression_fast(flat_x,0.3)
        # print(len(flat_x))
    if len(flat_x) == 0:
        print('Please retake the image, crop numbers only and align them horizontally')
        return
    def _sort_ymin(el):
        '''
        sort array based on position of element [xmin,ymin,xmax,ymax]
        '''
        return el[1]
    def _sort_xmin(el):
        '''
        sort array based on position of element [xmin,ymin,xmax,ymax]
        '''
        return el[0]

    flat_x.sort(key=_sort_ymin)    
    final = []
    lines = {}
    c = 0 # line number
    lines[c] = [flat_x[0]]
    mean_h = np.mean(np.array([(x[3] - x[1]) for x in flat_x]))
    mean_w = np.mean(np.array([(x[2] - x[0]) for x in flat_x]))
    thr_h = mean_h

    _ = 1
    for i in range(1,len(flat_x)):
        if flat_x[i][1] - lines[c][0][1] < thr_h:
            lines[c].append(flat_x[i])
            _ += 1  
        else:
            _ = 1
            c += 1
            lines[c] = [flat_x[i]]
    for k in list(lines.keys()):
        lines[k].sort(key=_sort_xmin)
        arr = []

        # for i in range(0,len(lines[k])-1):
        #     if abs(lines[k][i][2] - lines[k][i+1][0]) <= mean_w/3:
        #         arr.append('{}{}'.format(str(int(lines[k][i][-1])), str(int(lines[k][i+1][-1]))))
        # lines[k] = [str(int(t[-1])) for t in lines[k]]
        
        i = 0
        while i < len(lines[k])-1:
            if abs(lines[k][i][2] - lines[k][i+1][0]) <= mean_w/2:
                arr.append('{}{}'.format(str(int(lines[k][i][-1])), str(int(lines[k][i+1][-1]))))
                i+=1
            i+=1
        retake=False
        if len(arr) != 6:
            
            retake = True
        # a = ''.join(lines[k])
        # a = re.findall(r'\d{2}',a)
        final.append(arr)
    return final,retake


def get_text():
    
    company_lst = []
    date_lst = []
    number_result = []
   
    for img in glob.glob("/home/ubuntu/lotto/output_images/*.jpg"):
        split_text=os.path.splitext(img)
        file_name = os.path.splitext(img)[0]
        reader = easyocr.Reader(['es', 'en'], gpu=False)
        if '1' in file_name:
            company_result= reader.readtext(img, detail=0, paragraph=True)
            company_lst.append(company_result)
        if '2' in file_name:
            cvimg = cv2.imread(img)
            result = inference_detector(model, cvimg)
            number_result =print_line(result,thr = 0.5)
        if '3' in file_name:
            #reader = easyocr.Reader(['es', 'en'], gpu=True)
            date_result = reader.readtext(img, detail=0, paragraph=True)
            date_lst.append(date_result)
            print(date_lst)
    
    length = len(number_result)
    d = {}
    lst_temp  = []
    
    for i in range(length):
        d = {}
        if i < len(number_result):
            d["number"] = number_result[i]
        else:
            d["number"] = " "
        lst_temp.append(d)
    #print(lst_temp)
    index = {'company': company_lst,
                            'number': number_result,
                            'date': date_lst,
                            }
    all_details_json = json.dumps(index)
    print(all_details_json)
    
    textfile_name = "lottery_json"
    return all_details_json

def get_type_text(type_part_img):
    reader = easyocr.Reader(['es', 'en'], gpu=False)
    type_result = reader.readtext(type_part_img, detail=0, paragraph=True)
    return type_result

def get_number_text(number_part_img):
    result = inference_detector(model, number_part_img)
    list_img, bbox = split_img(number_part_img, show = False)
    results = []
    for _ in list_img:
        results.append(inference_detector(model, _))
    number_result = []
    for result in results:
        x,retake = print_line(result,thr = 0.5)
        if x:
            for _ in x:
                number_result.append(_)
        else:
            number_result.append(None)
    # number_result =print_line(result,thr = 0.5)
    return number_result

def get_date_text(date_part_img):
    reader = easyocr.Reader(['es', 'en'], gpu=False)
    date_result = reader.readtext(date_part_img, detail=0, paragraph=True)
    return date_result

# with open(textfile_name+".json", "w") as f:
#   try:
#     f.write(json.dump(all_details_json))
#   except:
#     f.write(str(all_details_json))
