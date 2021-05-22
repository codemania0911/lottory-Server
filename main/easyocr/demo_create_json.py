import json
import os
    
# import mmcv
from main.easyocr.mmdet.apis import (inference_detector,
                        init_detector, show_result_pyplot)
import matplotlib.pyplot as plt
from PIL import Image
import glob
import re
import numpy as np
import easyocr

# The file path of config file ocr.py and latest.pth
config_file = "./main/easyocr/weights/ocr.py"
checkpoint_file = './main/easyocr/weights/latest.pth'
model = init_detector(config_file, checkpoint_file, device='cpu')



# x = result[2]
def print_line(x,printline = True,thr = 0.5):
    '''
    x is the result of one image
    '''
    # take value > 0.6
    for i,_x in enumerate(x):
        x[i] = [_ for _ in _x if _[-1] > 0.6]

    for i,_x in enumerate(x):
        for j,__x in enumerate(_x):
            x[i][j] = np.append(x[i][j],i)

    flat_x = []
    for i in range(len(x)):
        for j in range(len(x[i])):
            flat_x.append(x[i][j])


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
    MEAN_H = np.mean([x[3] - x[1] for x in flat_x])

    line = {0:[flat_x[0]]}
    c = 0
    for i in range(1,len(flat_x)):
        if flat_x[i][1] - flat_x[i-1][1] < MEAN_H/2:
            line[c].append(flat_x[i])
        else:
            c+= 1
            line[c] = [flat_x[i]]
    for i in list(line.keys()):
        line[i].sort(key=_sort_xmin)

    final = []
    for i in list(line.keys()):
        final.append([str(int(x[-1])) for x in line[i]])
    _a = []
    for f in final:
        a = ''.join(f)
        a = re.findall(r'\d{2}',a)
        _a.append(a)
        if printline:
            print(a)
    return _a

def create_json():
    
    company_lst = []
    date_lst = []

    for img in glob.glob("./output_images/*.jpg"):
        split_text=os.path.splitext(img)
        file_name = os.path.splitext(img)[0]
        if '1' in file_name:
            reader = easyocr.Reader(['es', 'en'], gpu=True)
            company_result= reader.readtext(img, detail=0, paragraph=True)
            company_lst.append(company_result)
        if '2' in file_name:
            result = inference_detector(model, img)
            number_result =print_line(result,printline = True,thr = 0.5)
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
    return all_details_json

