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
import base64

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


def readb64(base64_string): 
    nparr = np.fromstring(base64.b64decode(base64_string), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


    
@csrf_exempt
def lotteryocrApi(request):
    data = request.POST["imgString"]
    imgString = data.encode().split(b';base64,')[-1]
    cvimg = readb64(imgString)
#     img = base64_to_PIL(imgString)
#     img = np.array(img)
        
    outpath = "./output_images"
    get_image_parts(cvimg, outpath)
    all_img_details = create_json()
           
    return JsonResponse(all_img_details, safe=False)

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
