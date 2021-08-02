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
import boto3



def detect_signature(response):
    '''
    fucntion to detect the information of signature
    1. Whether there is a signature in the signature section. But when it wraps only the signature, I wonder if it's detected.
    2. Check whether there is a "LSSL lotto club"  text next to the signature or not
    @isSignature: True if there is signature next to SIGNATURE column
    @isLSSL: True if there is LSSL signature next to written signature
    @signature_index: index of written signature in response["Blocks"]. It is 0 if there is no written signature
    '''
    line_index = 0
    signature_index = 0
    text_next_to_signature = ""
    isSignature = False
    isLSSL = False
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            line_index = line_index +1
            if item["Text"] == "SIGNATURE":
                text_next_to_signature = response["Blocks"][line_index +1]['Text']
                # print("sinature block", response["Blocks"][line_index +1])
                if text_next_to_signature == "Your ticket, not the playslip is your valid receipt. Check your ticket":
                    print("there is ***** no signature", str(line_index+1))                    
                else:
                    isSignature = True
                    if "LSSL" in text_next_to_signature:
                        isLSSL = True
                    signature_index = line_index+1
    return isSignature, isLSSL, signature_index

def find_index_LSSL(response):
    word_index = 0
    for item in response["Blocks"]:
        word_index = word_index +1
        if item["BlockType"] == "WORD":
            if item["Text"] == "LSSL":
                return word_index-1
    return word_index
                            
def detect_signature_bbx(signature_index, word_index, response):
    whole_signature_bbx = response["Blocks"][signature_index]["Geometry"]["BoundingBox"]
    if word_index==0:
        width = whole_signature_bbx["Width"] 
    else:
        LSSL_word_bbx = response["Blocks"][word_index]["Geometry"]["BoundingBox"]
        width = LSSL_word_bbx["Left"] - whole_signature_bbx["Left"]
    left = whole_signature_bbx["Left"]
    top = whole_signature_bbx["Top"]
    height = whole_signature_bbx["Height"]
    print("whole_signature_bbx",whole_signature_bbx)
    print("LSSL_word_bbx",LSSL_word_bbx)
    return left, top, width, height


def rotate_270(img):
    im2 = img.convert('RGBA')
    rot = im2.rotate(270, expand=1)
    # a white image same size as rotated image
    fff = Image.new('RGBA', rot.size, (255,)*4)
    # create a composite image using the alpha layer of rot as a mask
    out = Image.composite(rot, fff, rot)
    # save your work (converting back to mode='1' or whatever..)
    img = out.convert(img.mode)
    return img

def  detect_long_signature_bbx(signature_index,LSSL_word_index, response):
    whole_signature_bbx = response["Blocks"][signature_index]["Geometry"]["BoundingBox"]
    single_signature_index = find_index_long_signature(signature_index, response)    
    single_signature_bbx = response["Blocks"][single_signature_index]["Geometry"]["BoundingBox"]    
    LSSL_word_bbx = response["Blocks"][LSSL_word_index]["Geometry"]["BoundingBox"]      
    width = LSSL_word_bbx["Left"] - single_signature_bbx["Left"] - single_signature_bbx["Width"]
    left = single_signature_bbx["Left"] + single_signature_bbx["Width"]
    top = whole_signature_bbx["Top"]
    height = whole_signature_bbx["Height"]   
    return left, top, width, height

def find_index_long_signature(whole_sig_index, response):
    child_Ids = response["Blocks"][whole_sig_index]["Relationships"][0]["Ids"] # array
    word_index = 0
    for item in response["Blocks"]:
        word_index = word_index +1
        if item["BlockType"] == "WORD" and item["Text"] == "SIGNATURE":
            if response["Blocks"][word_index-1]['Id'] in child_Ids:
                return word_index-1
    return 0

def LSSL_text_check(text):
    input_txt = text.lower()
    if "lotto club" in input_txt or "lottery club" in input_txt:
        return True
    else:
        return False

def detect_long_signature(response):
    line_index = 0
    signature_index = 0
    isSignature = False
    isLSSL = False
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            line_index = line_index +1
            if ("SIGNATURE" in item["Text"] and "LSSL" in item["Text"]) or ("AREA CODE" in item["Text"] and "LSSL" in item["Text"]):         
                isSignature = True
                isLSSL = LSSL_text_check(item["Text"])
                signature_index = line_index
    return isSignature, isLSSL, signature_index

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
            #  ===== checking signature            
            documentName = s3_file1
            textract = boto3.client('textract', aws_access_key_id=AWS_ACCESS_KEY(),
                                                aws_secret_access_key=AWS_SECRET_KEY(), 
                                                region_name=AWS_REGION())
            # Call Amazon Textract
            response = textract.detect_document_text(
                Document={
                    'S3Object': {
                    'Bucket': AWS_BUCKET_NAME(),
                    'Name': documentName}})
            isSignature, isLSSL, signature_index = detect_signature(response)
            if isSignature:
                if isLSSL:                    
                    return JsonResponse({'result': "success"})
                else:
                    return JsonResponse({'result': "failed", 'data':"The text of LSSL lotto club is missing or wrong"})
            else:
                isSignature, isLSSL, signature_index = detect_long_signature(response)
                if isLSSL:                   
                        return JsonResponse({'result': "success"})                   
                else: 
                    if isSignature:
                        return JsonResponse({'result': "failed", 'data':"The text of LSSL lotto club is missing or wrong"})
                    else:                    
                        print("there is no signature")
                        return JsonResponse({'result': "failed", 'data':"Make sure it's in the signature column correctly."})
    except Exception as error:
        return JsonResponse({'result': str(error)})
    