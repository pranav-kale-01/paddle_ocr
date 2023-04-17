import io
import os
from paddleocr import PaddleOCR, draw_ocr
import cv2
import time
import requests
import json
from PIL import Image
from flask import Flask, request, jsonify
import traceback


import configparser
import pandas as pd

from flask_cors import CORS, cross_origin

config = configparser.ConfigParser()
v = config.read('./env.ini')

if not v:
        print("Aborting!! ini file not found")
        exit(0)

IMAGE_URL = config['SERVER']["IMAGE_URL"]
IMPORT_ITEM_URL = config['SERVER']["IMPORT_ITEM_URL"]
IMPORT_PO_URL = config['SERVER']["IMPORT_PO_URL"]
CSV_STORAGE_DIR = config['SERVER']["CSV_STORAGE_DIR"]

image_dir = config['SERVER']["IMAGE_DIR"]
out_dir = config['SERVER']["OUT_DIR"]
det_model_dir = config['SERVER']["DET_MODEL_DIR"]
rec_model_dir = config['SERVER']["REC_MODEL_DIR"]


ocr = PaddleOCR(use_angle_cls=True,
                det_model_dir=det_model_dir,
                rec_model_dir=rec_model_dir,
                use_gpu=False)


# FOR TESTING
# LOOPS OVER THE PROVIDED FOLDER AND RUNS OCR ON ALL THE IMAGES IN THAT FOLDER.
# RESULT OF THOSE IMAGES ARE SAVED IN "inference_results" DIRECTORY
def save_ocr(img_path, result):
    global out_dir
    save_path = os.path.join(out_dir, img_path.split('/')[-1])

    image = cv2.imread(img_path)

    boxes = [line[0] for line in result[0]]
    txts = [line[1][0] for line in result[0]]
    scores = [line[1][1] for line in result[0]]
    im_show = draw_ocr(image, boxes, txts, scores, font_path='./config/en_standard.ttf')
    x = cv2.imwrite(save_path, im_show)


def read_ocr(filename):
    original_filename = filename
    img_angles = [0, 90, 180, 270]
    for angle in img_angles:
        print('trying with image angle {}'.format(angle))
        if angle != 0:
            # set a new filename with angle
            fns = original_filename.split('/')
            fnp = '/'.join(fns[:-1])
            fn = fns[-1].split('.')
            filename = '{}/{}_{}.{}'.format(fnp, fn[0], angle, fn[1])

            im = Image.open(original_filename)
            im = im.rotate(angle, expand=True)
            im.save(filename)

        print(filename)
        _st = time.time()
        result = ocr.ocr(filename)
        print("RESULT", result)
        ocr_time = time.time() - _st

        ocr_arr = []
        for line in result[0]:
            ocr_arr.append(line[1][0])

        s = '^'.join(ocr_arr)

        save_ocr(filename, result)
        
        # breaking if we get required results
        if s != None: 
            break

    return s

# FLASK SERVER CODE 
def post_request(payload):
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    
        res= requests.post(IMPORT_ITEM_URL, data=json.dumps(payload), headers=headers)
        res_json = res.json()

        if res.status_code == 200:
            return jsonify( {"status" : "success", "message" : res_json['message'], "status_code" : res.status_code} )
        elif res.status_code == 201 or res.status_code == 204:
            if res_json['message'] == "Similar Items Found":
              return jsonify( {"status" : "success", "message" : res_json['message'], "status_code" : res.status_code, "similar_items" : res_json['data']} )
            else:
              return jsonify( {"status" : "success", "message" : res_json['message'], "status_code" : res.status_code} )
        else:
            return jsonify( {"status" : "failed", "data" : res.reason, "status_code" : res.status_code} )

    except Exception as e:
        print(e.with_traceback(e.__traceback__))
        return jsonify( {"status" : "failed", "error" : e.__str__() } )
    
app = Flask(__name__)
CORS(app, support_credentials=True)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        image =  request.files
        file_name = './request_image.jpg'
        file_name = 'Test.png'
        file = open(file_name, 'wb')
        file.write( image['image'].read() )
        file.close()

        result = read_ocr(file_name)

        return ( {
            "status": "success",
            "data" : result,
        })

    except:
        traceback.print_exc()
        data = { "status" : "failed" }
        return ( jsonify(data) )
    

if __name__=='__main__':
    # UNCOMMENT BELOW PART ONLY FOR TESTING PURPOSES
    # ocr_test()

    # UNCOMMENT BELOW PART ONLY FOR DEPLOYMENT PURPOSES
    app.run( host="127.0.0.1" )