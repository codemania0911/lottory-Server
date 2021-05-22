from django.shortcuts import render

# Create your views here.
from django.shortcuts import render,get_object_or_404,redirect
from django.utils import timezone
from django.contrib import auth
from django.contrib.auth.models import User
from .forms import UserInfoCreateForm
from .models import userinfo

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from apphelper.image import union_rbox,adjust_box_to_origin,base64_to_PIL
import numpy as np
import time
import os
import uuid
# from ocrmodel import  crnn_handle
from PIL import Image
import cv2
import matplotlib.pyplot as plt
from .mainocr import *
from .easyocr.demo_create_json import *

filelock='file.lock'
if os.path.exists(filelock):
   os.remove(filelock)

# Create your views here.


def signup(request):
    if request.method=="POST":
        if request.POST["userpwd"]==request.POST["usercpwd"]:
            user = userinfo.objects.create(
                name=request.POST["username"], password=request.POST["userpwd"]
            )

            return redirect('login')
        return render(request, 'Mainpage/signup.html')
    return render(request, 'Mainpage/signup.html', {})


def login(request):
    if request.method=="POST":
        registered_user = userinfo.objects.get(name=request.POST["username"], password=request.POST["userpwd"])
        if request.POST["username"]==registered_user.name and request.POST["userpwd"]==registered_user.password:
            return redirect('lotteryocr')
        
        return render(request, 'Mainpage/login.html')

    return render(request, 'Mainpage/login.html', {})


def home(request):
    return render(request, 'Mainpage/home.html', {})


def lotteryocr(request):
    return render(request, 'Mainpage/lotteryocr.html', {})


@csrf_exempt
def lotteryocrApi(request):
    print('--------------start')
    data = request.POST["imgString"]
    imgString = data.encode().split(b';base64,')[-1]
    # img = base64_to_PIL(imgString)
    # img = np.array(img)
        
    img = mpimg.imread('./Capture.jpg')
    outpath = "./output_images"

    print('----------------get part')
    get_image_parts(img, outpath)
    print('-------------====get part success')
    all_img_details = create_json()
    print(all_img_details)

        # img = np.array(img)
        # H,W = img.shape[:2]

        # category_of_items = []
        # all_img_details = {}
        # content_list =[]
        # outpath = ROOT_DIR + "/cropped/"
        # image_path = ROOT_DIR +'/Capture.JPG'
        # textfile_name = image_path.split(".")[0]
        # textfile_name = textfile_name.split("/")[-1] +".json"
        
        # get_image_parts(img,outpath  )
        # c_id = 0
        # cropped_images = glob(outpath +"*.png")
        # if len(cropped_images)==1:
        #     menu_text = tr.run(image_path)
        #     to_dump = getting_menu_details(menu_text, c_id)
        #     content_list.extend(to_dump)
        # else:
        #     for img in cropped_images: #reading all cropped images of detection    
        #             menu_text = tr.run(img)
        #             c_id +=1
        #             to_dump = getting_menu_details(menu_text, c_id)
        #             content_list.extend(to_dump)

        # all_img_details['TextDetections'] = content_list
        # remove_string = "rm " + outpath +"*"
        # os.system(remove_string)
        # with open(textfile_name, "w", encoding='utf-8') as f:
        #     try:
        #         f.write(json.dumps(all_img_details, ensure_ascii=False))
        #     except:
        #         f.write(str(all_img_details))
        # print("\n\n",all_img_details )
        # print("Wrote into " , textfile_name)
        # end_time = time.time()
        # Time_estimate = end_time - start_time
        # print("\n Processing time:", Time_estimate)    
           
    return JsonResponse(all_img_details)

def signup_create(request):
    if request.method=="POST":
        form=UserInfoCreateForm(request.POST)
        if form.is_valid():
            post=form.save(commit=False)
            post.id=request.id
            post.name=request.name
            post.save()
            return redirect('post detail',id=post.id)
        else:
            form=UserInfoCreateForm()
        return render(request,'Mainpage/UserInfo_create.html',{'form':form})
