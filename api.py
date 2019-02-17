#!/usr/bin/python3
import os, datetime
from flask import Flask
from flask import g
from flask import request, redirect
from flask import flash
from werkzeug.utils import secure_filename
import sqlite3
import json

#import unirest
#from urllib.request import Request, urlopen
import requests

import cloudinary
from cloudinary import uploader

cloudinary.config(
  cloud_name = 'dku6odlrx',
  api_key = '719974798677889',
  api_secret = '6RkpNRe-cV0SuD7FFCuIh85Y9n0'
)

app = Flask(__name__)

DATABASE = 'db.db'
UPLOAD_FOLDER = 'uploads'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        print("!")
    return db


def letters(input):
    valids = []
    for character in input:
        if character.isalpha():
            valids.append(character)
    return ''.join(valids)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        print("*")
        db.close()


@app.route('/')
def hello_world():
    return 'Hello world!'


def detectAndTranslateLanguage(ll):
    s = letters("+".join(ll))
    response = requests.get("https://microsoft-azure-translation-v1.p.rapidapi.com/Detect?text=" + s,
                           headers={
                               "X-RapidAPI-Key": "d18d84006cmsh404865c0a044e37p1a8037jsn317de1042bc3",
                               "Accept": "application/json"
                           })
    '''
    response = unirest.get("https://microsoft-azure-translation-v1.p.rapidapi.com/Detect?text=" + s,
                           headers={
                               "X-RapidAPI-Key": "d18d84006cmsh404865c0a044e37p1a8037jsn317de1042bc3",
                               "Accept": "application/json"
                           }
                           )'''
    if response.code >= 500:
        return "Server Error\n"
    elif response.code >= 400:
        return "User Input Error\n"
    else:
        body = str(response.body)
        lang = body.split(">")[1].split("<")[0]
        if 'en' not in lang:
            response = requests.get(
                    "https://microsoft-azure-translation-v1.p.rapidapi.com/translate?to=en&text=" + s,
                    headers={
                        "X-RapidAPI-Key": "d18d84006cmsh404865c0a044e37p1a8037jsn317de1042bc3"
                    }
                )
            '''
            response = unirest.get(
                "https://microsoft-azure-translation-v1.p.rapidapi.com/translate?to=en&text=" + s,
                headers={
                    "X-RapidAPI-Key": "d18d84006cmsh404865c0a044e37p1a8037jsn317de1042bc3"
                }
                )'''
            if response.code >= 500:
                return "Server Error\n"
            elif response.code >= 400:
                return "User Input Error\n"
            else:
                body = str(response.body)
                result = body.split(">")[1].split("<")[0]
                lll = result.split(" ")
                return lll
        else:
            return ll



def extractNameFromFrontImage(imagefile):
    if imagefile:
        path = os.path.join(UPLOAD_FOLDER, str(datetime.datetime.now().strftime("%Y-%m-%d")))
        if not os.path.exists(path):
            os.makedirs(path)
        filename = str(datetime.datetime.now())
        image_link = os.path.join(path, filename)
        imagefile.save(image_link)
        db = get_db()
        cur = db.cursor()
        sql = "INSERT INTO Images (filename, imagelink) VALUES (?, ?);"
        cur.execute(sql,(filename, image_link))
        db.commit()
        cur.close()

        response = cloudinary.uploader.upload("deneme.jpg", ocr="adv_ocr")
        if response['info']['ocr']['adv_ocr']['status'] == 'complete':
            data = response['info']['ocr']['adv_ocr']['data']
            ann = data[0]["textAnnotations"]
            result = ""
            max_area = 0
            for d in ann:
                if "\n" in d["description"]:
                    continue
                x1 = d["boundingPoly"]["vertices"][0]['x']
                y1 = d["boundingPoly"]["vertices"][0]['y']
                x2 = d["boundingPoly"]["vertices"][1]['x']
                y2 = d["boundingPoly"]["vertices"][2]['y']
                area = (x2 - x1) * (y2 - y1)
                if area > max_area:
                    result = d["description"]
                    max_area = area
            print(result)
            return json.dumps({'name':result})
        else:
            return 'No Success'


def getWordsFromBody(body):
    # The following code sucks because the response we get from the API sucks more!!!!!!!!!!!!
    all_words = []
    for i in range(len(body["regions"])):
        for j in range(len(body["regions"][i]["lines"])):
            for k in range(len(body["regions"][i]["lines"][j])):
                for t in range(len(body["regions"][i]["lines"][j]["words"])):
                    text = body["regions"][i]["lines"][j]["words"][t]["text"]
                    text = text.encode('utf-8')
                    text = str(text).lower()
                    all_words.append(text)
    return all_words


@app.route('/extract', methods=['POST'])
def extractFromImage():
    if 'imagefront' not in request.files or 'imageback' not in request.files:
        flash('No file part')
        redirect(request.url)
    imagefront = request.files['imagefront']
    extractNameFromFrontImage(imagefront)
    imagefile = request.files['imageback']
    if imagefile:
        #filename = secure_filename(imagefile.filename)
        path = os.path.join(UPLOAD_FOLDER, str(datetime.datetime.now().strftime("%Y-%m-%d")))
        if not os.path.exists(path):
            os.makedirs(path)
        filename = str(datetime.datetime.now())
        image_link = os.path.join(path, filename)
        imagefile.save(image_link)
        db = get_db()
        cur = db.cursor()
        sql = "INSERT INTO Images (filename, imagelink) VALUES (?, ?);"
        cur.execute(sql,(filename, image_link))
        db.commit()
        cur.close()

        response = requests.post(
            "https://microsoft-azure-microsoft-computer-vision-v1.p.rapidapi.com/ocr?language=en&detectOrientation=true",
            headers={
                "X-RapidAPI-Key": "d18d84006cmsh404865c0a044e37p1a8037jsn317de1042bc3"
            },
            files={
                "file": open(image_link, mode="rb")
            }
        )
        '''
        response = unirest.post(
            "https://microsoft-azure-microsoft-computer-vision-v1.p.rapidapi.com/ocr?language=en&detectOrientation=true",
            headers={
                "X-RapidAPI-Key": "d18d84006cmsh404865c0a044e37p1a8037jsn317de1042bc3"
            },
            params={
                "file": open(image_link, mode="r")
            }
            )'''

        if response.code >= 500:
            return "Server Error\n"
        elif response.code >= 400:
            return "User Input Error\n"
        else:
            all_words = getWordsFromBody(response.body)
            all_words = detectAndTranslateLanguage(all_words)
            name = None
            dosage = None
            freq = None
            max = None
            last_text = None
            last_number = None
            for text in all_words:
                if "times" in text:
                    if freq is None:
                        freq = (last_text + " times")
                if "dose" in text or "dosage" in text or "tablet" in text:
                    if isinstance(last_number, int):
                        if dosage is None:
                            dosage = last_number
                if text.isdigit():
                    if "dose" in last_text or "dosage" in last_text or "tablet" in last_text:
                        if dosage is None:
                            dosage = int(text)
                        last_number = None
                        last_text = None
                    elif "exceed" in last_text:
                        max = int(text)
                        last_number = None
                        last_text = None
                    else:
                        last_number = int(text)
                        last_text = None
                else:
                    last_text = text
                    last_number = None
            json_string = {}
        json_string["name"] = name
        json_string["dosage"] = dosage
        json_string["frequency"] = freq
        json_string["max"] = max
        return json.dumps(json_string)

@app.route('/oldExtract', methods=['POST'])
def oldExtractFromImage():
    if 'imagefile' not in request.files:
        flash('No file part')
        redirect(request.url)
    imagefile = request.files['imagefile']
    if imagefile:
        #filename = secure_filename(imagefile.filename)
        path = os.path.join(UPLOAD_FOLDER, str(datetime.datetime.now().strftime("%Y-%m-%d")))
        if not os.path.exists(path):
            os.makedirs(path)
        filename = str(datetime.datetime.now())
        image_link = os.path.join(path, filename)
        imagefile.save(image_link)
        print("HEY")
        db = get_db()
        cur = db.cursor()
        sql = "INSERT INTO Images (filename, imagelink) VALUES (?, ?);"
        cur.execute(sql,(filename, image_link))
        db.commit()
        cur.close()

        response = requests.post(
            "https://microsoft-azure-microsoft-computer-vision-v1.p.rapidapi.com/ocr?language=en&detectOrientation=true",
            headers={
                "X-RapidAPI-Key": "d18d84006cmsh404865c0a044e37p1a8037jsn317de1042bc3"
            },
            files={
                "file": open(image_link, mode="rb")
            }
        )
        '''
        response = unirest.post(
            "https://microsoft-azure-microsoft-computer-vision-v1.p.rapidapi.com/ocr?language=en&detectOrientation=true",
            headers={
                "X-RapidAPI-Key": "d18d84006cmsh404865c0a044e37p1a8037jsn317de1042bc3"
            },
            params={
                "file": open(image_link, mode="r")
            }
            )'''

        if response.code >= 500:
            return "Server Error\n"
        elif response.code >= 400:
            return "User Input Error\n"
        else:
            body = response.body
            # The following code sucks because the response we get from the API sucks more!!!!!!!!!!!!
            name = None
            dosage = None
            freq = None
            max = None
            last_text = None
            last_number = None
            for i in range(len(body["regions"])):
                for j in range(len(body["regions"][i]["lines"])):
                    for k in range(len(body["regions"][i]["lines"][j])):
                        for t in range(len(body["regions"][i]["lines"][j]["words"])):
                            text = body["regions"][i]["lines"][j]["words"][t]["text"]
                            text = text.encode('utf-8')
                            text = str(text).lower()
                            if "times" in text:
                                if freq is None:
                                    freq = (last_text + " times")
                            if "dose" in text or "dosage" in text or "tablet" in text:
                                if isinstance(last_number, int):
                                    if dosage is None:
                                        dosage = last_number
                            if text.isdigit():
                                if "dose" in last_text or "dosage" in last_text or "tablet" in last_text:
                                    if dosage is None:
                                        dosage = int(text)
                                    last_number = None
                                    last_text = None
                                elif "exceed" in last_text:
                                    max = int(text)
                                    last_number = None
                                    last_text = None
                                else:
                                    last_number = int(text)
                                    last_text = None
                            else:
                                last_text = text
                                last_number = None
        json_string = {}
        json_string["name"] = name
        json_string["dosage"] = dosage
        json_string["frequency"] = freq
        json_string["max"] = max
        return json.dumps(json_string)

@app.route('/close')
def bye_world():
    close_connection(0)
    return 'Bye world!'


app.run(host='0.0.0.0', port= 5000)