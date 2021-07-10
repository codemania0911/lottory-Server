from django.shortcuts import render

# Create your views here.

from PIL import Image
from .Preprocessing import convert_to_image_tensor, invert_image
import torch
from .Model import SiameseConvNet, distance_metric
from io import BytesIO
import json
import math, re, os, base64, six, io
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date, timedelta
import boto3
from lotteryOCR.aws_config import *

def load_model():
    device = torch.device('cpu')
    model = SiameseConvNet().eval()
    model.load_state_dict(torch.load('/home/ubuntu/lotto/signatureVerify/weights/model_large_epoch_20', map_location=device))
    return model

@csrf_exempt
def signatureVerify(request):
    try:
        if request.method == "POST":
            data_lotto = request.POST["lottery_imgString"]
            data_mobile = request.POST["mobile_imgString"]
            data_lotto = re.sub(' ', '+', str(data_lotto))                   
            data_mobile = re.sub(' ', '+', str(data_mobile))                   
            lotto_imgString = data_lotto.encode().split(b';base64,')[-1]
            mobile_imgString = data_mobile.encode().split(b';base64,')[-1]
            lotto_imgdata = base64.b64decode(lotto_imgString)
            mobile_imgdata = base64.b64decode(mobile_imgString)
            output_lotto = six.BytesIO()
            output_mobile = six.BytesIO()
            output_lotto = lotto_imgdata
            output_mobile = mobile_imgdata

            # =====   uploading images
            ftime = datetime.now().strftime('%Y%m%d%H%M%S%f')
            s3 = boto3.resource(
                's3', aws_access_key_id=AWS_ACCESS_KEY(), aws_secret_access_key=AWS_SECRET_KEY())
            # == lottery signature upload
            s3_file1 = "lotto_sig" + str(ftime)+".jpg"    
            obj = s3.Object(AWS_BUCKET_NAME(), s3_file1)
            obj.put(Body=output_lotto)
            obj_acl = s3.ObjectAcl(AWS_BUCKET_NAME(), s3_file1)
            obj_acl.put(ACL='public-read')
            # === mobile signature upload
            s3_file2 = "mobile_sig" + str(ftime)+".jpg"    
            obj = s3.Object(AWS_BUCKET_NAME(), s3_file2)
            obj.put(Body=output_mobile)
            obj_acl = s3.ObjectAcl(AWS_BUCKET_NAME(), s3_file2)
            obj_acl.put(ACL='public-read')

            # ==== comparison signature
            input_image = Image.open(io.BytesIO(lotto_imgdata))
            input_image_tensor = convert_to_image_tensor(invert_image(input_image)).view(1,1,220,155)
            mobile_image = Image.open(io.BytesIO(mobile_imgdata))
            mobile_image_tensor = convert_to_image_tensor(invert_image(mobile_image)).view(1,1,220,155)
            model = load_model()    
            anci = mobile_image_tensor
            f_A, f_X = model.forward(anci, input_image_tensor)
            dist = float(distance_metric(f_A, f_X).detach().numpy())
            threshold = 0.155139
            if dist <= threshold:  # Threshold obtained using Test.py
                # two signatures are matched
                print("dist", dist)
                return JsonResponse({'result': "success", 'threshold':str(threshold), 'dist_value':str(dist)})
            else: # not match
                print("failed")
                return JsonResponse({'result': "failed", 'threshold':str(threshold), 'dist_value':str(dist)})
    except Exception as error:
        return JsonResponse({'result': str(error)})
    