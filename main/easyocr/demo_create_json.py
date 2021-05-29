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
    flat_x = non_max_suppression_fast(flat_x,0.5)
        # print(len(flat_x))
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
    # MEAN_H = np.mean([x[3] - x[1] for x in flat_x])

    # line = {0:[flat_x[0]]}
    # c = 0
    # for i in range(1,len(flat_x)):
    #     if flat_x[i][1] - flat_x[i-1][1] < MEAN_H/2:
    #         line[c].append(flat_x[i])
    #     else:
    #         c+= 1
    #         line[c] = [flat_x[i]]
    # for i in list(line.keys()):
    #     line[i].sort(key=_sort_xmin)

    # final = []
    # for i in list(line.keys()):
    #     final.append([str(int(x[-1])) for x in line[i]])
    # _a = []
    # for f in final:
    #     a = ''.join(f)
    #     a = re.findall(r'\d{2}',a)
    #     _a.append(a)
    #     if printline:
    #         print(a)
    # return _a
    final = []
    n_row = len(flat_x) // 12
    for c in range(0,n_row):
        temp = flat_x[c*12:(c+1)*12]
        temp.sort(key=_sort_xmin)
        temp = [str(int(t[-1])) for t in temp]
        a = ''.join(temp)
        a = re.findall(r'\d{2}',a)
        final.append(a)
    return final


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

def get_number_text(number_part_img):
    result = inference_detector(model, number_part_img)
    number_result =print_line(result,thr = 0.5)
    return number_result

# with open(textfile_name+".json", "w") as f:
#   try:
#     f.write(json.dump(all_details_json))
#   except:
#     f.write(str(all_details_json))
