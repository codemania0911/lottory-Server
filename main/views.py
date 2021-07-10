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
    outpath = "./output_images"
    get_image_parts(cvimg, outpath)
    all_img_details = get_text()
           
    return JsonResponse(all_img_details, safe=False)

@csrf_exempt
def lotteryocrpartsApi(request):
    try:
        type_text = ''
        number_text = ''
        date_text = ''
        numberImage = request.POST["numberImage"]
        numberImageStr = numberImage.encode().split(b';base64,')[-1]
        numbercvimg = readb64(numberImageStr)       
        number_text = get_number_text(numbercvimg)
        
        if request.POST.get("typeImage") or request.POST.get("dateImage"):
            reader = easyocr.Reader(['es', 'en'], gpu=False)
        
        
        if request.POST.get("typeImage"):
            typeImage = request.POST["typeImage"]
            typeImageStr = typeImage.encode().split(b';base64,')[-1]
            typecvimg = readb64(typeImageStr)   
            type_text = reader.readtext(typecvimg, detail=0, paragraph=True)
        if request.POST.get("dateImage"):
            dateImage = request.POST["dateImage"]
            dateImageStr = dateImage.encode().split(b';base64,')[-1]
            datecvimg = readb64(dateImageStr) 
            date_text = reader.readtext(datecvimg, detail=0, paragraph=True)
        result_data = {"type_text":type_text,"number_text":number_text,"date_text":date_text}
        return JsonResponse({"data":result_data}, safe=False)
    except Exception as error:
        return JsonResponse({"data": str(error)})

@csrf_exempt
def lotteryocrtypeApi(request):
    try:
        data = request.POST["imgString"]
        imgString = data.encode().split(b';base64,')[-1]
        cvimg = readb64(imgString)       
        type_text = get_type_text(cvimg)
        return JsonResponse({"data":type_text}, safe=False)
    except Exception as error:
        return Response({"data": str(error)})

@csrf_exempt
def lotteryocrnumberApi(request):
    try:
        data = request.POST["imgString"]
        imgString = data.encode().split(b';base64,')[-1]
        cvimg = readb64(imgString)  
#         cv2.imwrite("./output_images/test.jpg", cvimg)
        number_text = get_number_text(cvimg)
        return JsonResponse({"data":number_text}, safe=False)
    except Exception as error:
        return JsonResponse({"data": str(error)})

@csrf_exempt
def lotteryocrdateApi(request):
    try:
        data = request.POST["imgString"]
        imgString = data.encode().split(b';base64,')[-1]
        cvimg = readb64(imgString)       
        date_text = get_date_text(cvimg)
        return JsonResponse({"data":date_text}, safe=False)
    except Exception as error:
        return JsonResponse({"data": str(error)})
    
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
