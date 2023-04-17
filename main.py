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
import ocr_regex

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
            # print(line[1][0], end=" ")

        s = '^'.join(ocr_arr)

        save_ocr(filename, result)
        final_batch_number = ocr_regex.regex_final(s)

        # decoding with ascii to remove unecessary characters line \uff08
        # s = s.encode("ASCII", 'ignore').decode("ASCII", 'ignore')

        # writing the results in result file
        f = open("{}/ocr_results.txt".format(out_dir), "a", encoding='utf-8')
        f.write('filename: {}\nfinal_batch_number: {}\ntime - {} - {}\nfull ocr text: {}\n\n'.format(filename, final_batch_number, time.time() - _st, ocr_time, s))
        f.close()

        # print(final_batch_number)

        if final_batch_number == "" or final_batch_number is None:
            # repeat with new angle rotation
            pass
        else:
            return final_batch_number

    return ""


def ocr_test():
    # iterating through all the images in image_dir
    files = os.listdir(image_dir)

    skip_count = -1  ## CHANGE THIS TO THE FILE NUMBER YOU WANT TO SKIP
    do_only = ""  ## CHANGE THIS TO THE FILE NUMBER YOU WISH TO RUN OCR WITH (THIS FIELD TAKES ONLY ONE INPUT)
    count = 0

    for i in files:
        count += 1

        if count < 91 :
            continue

        if skip_count > count and skip_count != -1:
            continue

        if do_only != i and do_only != "":
            continue

        filename = f'{image_dir}{i}'
        s = read_ocr(filename)
        print(s)


# FLASK SERVER CODE
def post_request(payload):
    try:
        headers = {
            'Accept': 'application/json',
            # 'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIzIiwianRpIjoiYmE3M2Q3OWFmZGMxZjBlODNiZDVkYzUyMWFmYzFlYjEzMTljMjE5MWI2NWJmMjQ5N2Q2NjlmMGJkZTRkNjg0ZmI1NzA1ZTJlMWE1YzY4NjciLCJpYXQiOjE2NjUyOTQxNDIsIm5iZiI6MTY2NTI5NDE0MiwiZXhwIjoxNjk2ODMwMTQyLCJzdWIiOiI1NyIsInNjb3BlcyI6W119.PT9ouLHwLtwSkd1Xcrgwl369ieDwWAgdR6pmJN2app5Jlr-0_4OUPK0mAI6BhbYQmgfqMASykpyAfauLlhYXr5KQ1OViqZO64XVz8UnlKImvpuyUQ1Tkb0lmamO0oAX6xgGTHz5nAFasHGgWqNiIEeY807Gc92atJxNRCt6YJ8HMWd59d3VIydM5L2y5vvm8f5CSa9QPOnLvZymj8n7uQAlwks_opf94al8ZpxShaqgwraStVkIKEnA4wRTshnTqef-eGsBnc0JVW9UVSL9GVPrfUyUoDXA-8mVoWjMcw9wVAcs5M2hjTOG39Ryc7qgo5VhHUM_afZtbSE0FBoxkTk4aYFNK--Xprirz2vhNOl68O4TPHYUqF17O827depc418iztpYFbBu4kSnuU5Y0NMXxnllfhv0ujR4amigqaiZu9p3jt_zeDiyluEjX2l2O2N_bQZ0oGyh9YLNWvVNmHl8N5XoNOJvh3SoMKcJkVLMigUZGmncml-GzM5g7AJVfunuBHGkMVmgvE_qJKpsC0hcrhfh5acYdT6sskoXZo2qZdgiJNOdUDjssD4P02NFefS_s1UUag_tGuy1eq_yNBSs-rKCwovrU2Hdu_km5e-JQzEXAT4kFkoyybNBcLee3PcPaZZYx4qnq-8Tr0QGSq2LyZ5r3s1pDz6vX0_4_-xM',
            'Content-Type': 'application/json'
        }

        # print(json.dumps(payload))

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
    # return {"batch_number": "2NA0019"}
    try:
        image =  request.files
        other_data = request.form
        payload = {}

        file_name = './request_image.jpg'
        file_name = 'Test.png'
        file = open(file_name, 'wb')
        file.write( image['image'].read() )
        file.close()


        # image_dir = "./ocr_test/inference_results/request_image.jpg"
        # det_model_dir="./ch_PP-OCRv3_det_infer"
        # rec_model_dir = "./ch_PP-OCRv3_rec_infer"
        # out_path = "./ocr_test/inference_results"

        # output = subprocess.check_output( f"python -u tools/infer/predict_system.py --image_dir={image_dir} --det_model_dir={det_model_dir} --rec_model_dir={rec_model_dir} --use_gpu=False", shell=True )
        # batch_number = output.decode('ASCII').strip('\n').strip('\r')
        batch_number = read_ocr(file_name)

        if batch_number:
            payload['csv_id'] = other_data['csv_id']
            payload['batch_number'] = batch_number

            request_response = post_request( payload )

            print( request_response.json )

            if( request_response.json['message'] == "Similar Items Found" ):
              return ( {
                  "status": "success",
                  "batch_number" : batch_number,
                  "message" : request_response.json['message'],
                  "status_code" : request_response.json['status_code'],
                  "data" : request_response.json['similar_items']
              })
            elif( request_response.json['status'] == "failed" ):
              return jsonify( {  "status": "failed", "error" : request_response.json['error']} )
            else:
              return ( {
                  "status": "success",
                  "batch_number" : batch_number,
                  "message" : request_response.json['message'],
                  "status_code" : request_response.json['status_code'],
              })
        else:
            return jsonify( { "status": "failed", "error" : "no batch number detected"} )

    except:
        traceback.print_exc()

        data = {
            "status" : "failed",
        }
        return ( jsonify(data) )

@app.route('/upload_csv', methods=['POST'])
@cross_origin(supports_credentials=True)
def upload_csv():       
    other_data = request.form
    csv_file = request.files
    user_id = other_data['user_id']

    filename = f"{CSV_STORAGE_DIR}/{csv_file['csv_file'].filename}"
    file_extension = csv_file['csv_file'].filename.split(".")[-1]

    file = open(filename, 'wb')
    file.write( csv_file['csv_file'].read() )
    file.close()

    print( filename )

    try:
        # first sending the request to api to save the csv file 
        url = IMPORT_PO_URL

        # headers for import_po API
        request_headers = {
            'Accept': 'application/json'
        }
        payload={'id': user_id}
        files=[
            ('file', ( csv_file['csv_file'].filename,open(filename,'rb'), 'text/csv') )
        ]
        response = requests.request("POST", url, headers=request_headers, data=payload, files=files)
        csv_id = response.json()['id']

        # now csv is saved in database, adding the items usnig import_item API
        # headers for import_item API
        request_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        df = None
        if file_extension.lower() == 'xlsx':
            df = pd.read_excel(filename, engine='openpyxl')
        elif file_extension.lower() == 'xls':
            toread = io.BytesIO()
            toread.write(open(filename, 'rb').read())  # pass your `decrypted` string as the argument here
            toread.seek(0)  # reset the pointer

            df = pd.read_excel(toread, engine='xlrd')
        elif file_extension.lower() == 'csv':
            df = pd.read_csv(filename)

        extracted_rows = []
        headers = df.keys()

        for i in df.values:
            count = 0
            matches = {
                "order_qty" : "",
                "item_name" : "",
                "batch_num" : "",
                "exp_date" : "",
                "mfg_date" : "",
                "mrp" : "[]",
            }

            for j in i:
                header_name = headers[count].__str__()

                if( header_name.lower().__contains__("qty") or header_name.lower().__contains__( "quantity" ) ):
                    if( j != 0 ):
                        matches["order_qty"] = j.__str__().strip()

                if( header_name.lower().strip() == "mrp" ):
                    if( float(j) != 0.0 ):
                        matches["mrp"] = j 

                if( header_name.lower().__contains__("date") or header_name.lower().__contains__( "mfgdate" ) ):
                    if( len( j.__str__() ) > 2 and j.__str__() != "nan" ):
                        matches["mfg_date"] = j.__str__().strip()

                if( header_name.lower().__contains__("exp") or header_name.lower().__contains__( "expiry" ) ):
                    if( len( j.__str__() ) > 2 and j.__str__() != "nan" ):
                        matches["exp_date"] =  j.__str__().strip() 

                if( (header_name.lower().__contains__("prod") and header_name.lower().__contains__( "name" )) or header_name.lower().__contains__( "item" ) ):
                    if( j.__str__() != "nan" ):
                        matches["item_name"] = j.__str__().strip()

                if( header_name.lower().__contains__("batch") or header_name.lower().__contains__( "bno" ) ):
                    if( len( j.__str__() ) > 2):
                        matches["batch_num"] = j.__str__().strip()

                matches['csv_id'] = csv_id        
                count+=1

            payload = json.dumps([matches])
            extracted_rows.append( matches )

            response = requests.post(IMPORT_ITEM_URL, headers=request_headers, data=payload,  timeout=2.0)
            if( response.status_code == 200 ):
                print( response.status_code )
            else:
                print( response.reason )


        return jsonify( { "status": "success", "data" : extracted_rows} )

    except Exception as e:
        print( e )
        print( e.with_traceback( e.__traceback__ ) ) 

        return jsonify( { "status": "failed", "error" : e} )

if __name__=='__main__':
    # UNCOMMENT BELOW PART ONLY FOR TESTING PURPOSES
    # ocr_test()

    # UNCOMMENT BELOW PART ONLY FOR DEPLOYMENT PURPOSES
    app.run( host="127.0.0.1" )