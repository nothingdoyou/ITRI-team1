from __future__ import unicode_literals
from urllib import parse
import string
from flask import Flask, request, abort, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, PostbackEvent, PostbackTemplateAction, TemplateSendMessage, ButtonsTemplate, MessageTemplateAction
import requests
import json
import configparser
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
from bs4 import BeautifulSoup

# 1.setup log path and create log directory
logName = 'MyProgram.log'
logDir = 'log'
logPath = logDir + '/' + logName

# create log directory
os.makedirs(logDir, exist_ok=True)

# 2.create logger, then setLevel
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

# 3.create file handler, then setLevel
# create file handler
fileHandler = logging.FileHandler(logPath, mode='w')
fileHandler.setLevel(logging.DEBUG)

# 4.create stram handler, then setLevel
# create stream handler
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)

# 5.create formatter, then handler setFormatter
AllFormatter = logging.Formatter(
    '[%(levelname)s][%(asctime)s][LINE:%(lineno)s][%(module)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(AllFormatter)
streamHandler.setFormatter(AllFormatter)

# 6.logger addHandler
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)

app = Flask(__name__, static_url_path='/static')
UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])


config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))
my_line_id = config.get('line-bot', 'my_line_id')
end_point = config.get('line-bot', 'end_point')
line_login_id = config.get('line-bot', 'line_login_id')
line_login_secret = config.get('line-bot', 'line_login_secret')
my_phone = config.get('line-bot', 'my_phone')
HEADER = {
    'Content-type': 'application/json',
    'Authorization': f'Bearer {config.get("line-bot", "channel_access_token")}'
}


# ========================================================

all_astros = {"牡羊座": 0, "金牛座": 1, "雙子座": 2, "巨蟹座": 3, "獅子座": 4, "處女座": 5, "天秤座": 6, "天蠍座": 7, "射手座": 8, "魔羯座": 9, "水瓶座": 10, "雙魚座": 11
              }

# ========================================================
# all_timepool = {"今日": 0, "明日": 1, "本周": 2, "本月": 3}


@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        return 'ok'
    body = request.json
    events = body["events"]
    if request.method == 'POST' and len(events) == 0:
        return 'ok'
    logger.info(body)
    print(body)
    if "replyToken" in events[0]:
        payload = dict()
        replyToken = events[0]["replyToken"]
        payload["replyToken"] = replyToken
        if events[0]["type"] == "message":
            if events[0]["message"]["type"] == "text":
                text = events[0]["message"]["text"]

                if text == "我的名字":
                    payload["messages"] = [getNameEmojiMessage()]
                elif text == "出去玩囉":
                    payload["messages"] = [getPlayStickerMessage()]
                elif text == "台北101":
                    payload["messages"] = [getTaipei101ImageMessage(),
                                           getTaipei101LocationMessage(),
                                           getMRTVideoMessage()
                                           ]
                elif text == "quoda":
                    payload["messages"] = [
                        {
                            "type": "text",
                            "text": getTotalSentMessageCount()
                        }
                    ]
                elif text == "今日確診人數":
                    payload["messages"] = [
                        {
                            "type": "text",
                            "text": getTodayCovid19Message()
                        }
                    ]

# =============================================================

                elif text == "星座運勢":
                    payload["messages"] = [reply_astros_table()]

                # elif text in all_astros:
                #     payload["messages"] = [reply_time_selecter()]

                # elif text == "水瓶座":
                #     payload["messages"] = [reply_message_astro()]

                # elif text in all_astros:
                #     payload["messages"] = [reply_tomorrow_content()]

# =============================================================
                else:
                    payload["messages"] = [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                replyMessage(payload)
            elif events[0]["message"]["type"] == "location":
                logger.info(events[0]["message"])
                title = events[0]["message"]["title"]
                latitude = events[0]["message"]["latitude"]
                longitude = events[0]["message"]["longitude"]
                payload["messages"] = [
                    getLocationConfirmMessage(title, latitude, longitude)]
                logger.info(payload)
                replyMessage(payload)

# =============================================

        elif events[0]["type"] == "postback":
            # selected_astro = ''
            # selected_time = ''
            # print(events[0]["postback"])

            if "data" in events[0]["postback"]:
                with open("./json/Astro_data.json", 'r') as f:
                    json_data = json.load(f)
                firstData = events[0]["postback"]["data"][0:2]
                userAstro = events[0]["postback"]["data"][3:6]
                # selectTime = events[0]["postback"]["data"]

                if firstData == "AS":
                    json_data["selected_astro"] = userAstro

                    with open("./json/Astro_data.json", "w") as f:
                        json.dump(json_data, f)

                    # print('=================')
                    # print(payload)
                    # print(json_data)
                    # print(userAstro)
                    # print('=================')
                    payload["messages"] = [reply_time_selecter()]
                    replyMessage(payload)
                elif firstData == "TM":
                    json_data["selected_time"] = events[0]["postback"]["data"][3:5]

                    with open("./json/Astro_data.json", "w") as f:
                        json.dump(json_data, f)

                    # print("+"*20)
                    # print("ok")
                    # print(json_data)
                    # print("+"*20)
                    payload["messages"] = [reply_result_message()]
                    replyMessage(payload)

            #     payload["messages"] = [reply_message_astro()]
            # replyMessage(payload)

            # if events[0]["postback"]["data"] in all_astros:
            #     payload["messages"] = [reply_time_selecter()]

            # if events[0]["postback"]["data"] in all_timepool and selected_astro in all_astros:
            # if events[0]["postback"]["data"] in all_timepool:
            #     selected_time = events[0]["postback"]["data"]
            #     payload["messages"] = [reply_message_astro()]

            #     replyMessage(payload)


# =============================================

            # if "params" in events[0]["postback"]:
            #     reservedTime = events[0]["postback"]["params"]["datetime"].replace(
            #         "T", " ")
            #     payload["messages"] = [
            #         {
            #             "type": "text",
            #             "text": F"已完成預約於{reservedTime}的叫車服務"
            #         }
            #     ]
            #     replyMessage(payload)
            # else:
            #     data = json.loads(events[0]["postback"]["data"])
            #     logger.info(data)
            #     action = data["action"]
            #     if action == "get_near":
            #         data["action"] = "get_detail"
            #         payload["messages"] = [getCarouselMessage(data)]
            #     elif action == "get_detail":
            #         del data["action"]
            #         payload["messages"] = [getTaipei101ImageMessage(),
            #                                getTaipei101LocationMessage(),
            #                                getMRTVideoMessage(),
            #                                getCallCarMessage(data)]
            #     replyMessage(payload)

    return 'OK'

# 有人來call這個路徑，就執行def callback


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return 'OK'


@app.route("/push", methods=['POST'])
def push():
    try:
        msg = request.args.get('msg')
        if msg != None:
            line_bot_api.push_message(my_line_id, TextMessage(text=msg))
            return msg
        else:
            return "OK"
    except:
        print('error')


# 若有接收到MessageEvent的話，call這裡


@handler.add(MessageEvent, message=TextMessage)
def pretty_echo(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )


@app.route("/sendTextMessageToMe", methods=['POST'])
def sendTextMessageToMe():
    pushMessage({})
    return 'OK'


# ========================================================
# all_astros = {"牡羊座": 0, "金牛座": 1, "雙子座": 2, "巨蟹座": 3, "獅子座": 4, "處女座": 5, "天秤座": 6, "天蠍座": 7, "射手座": 8, "摩羯座": 9, "水瓶座": 10, "雙魚座": 11
#               }

def reply_astros_table():
    with open("./json/1. astros_list.json", 'r', encoding='utf-8') as f:
        message = json.load(f)

    return message


def reply_time_selecter():
    with open("./json/2. time_selector.json", 'r', encoding='utf-8') as f:
        message = json.load(f)

    return message


def reply_result_message():
    with open("./json/Astro_data.json") as f:
        json_data = json.load(f)
    iuput_data = json_data

    if iuput_data["selected_astro"] in all_astros:
        your_astro = iuput_data["selected_astro"]
        time_selection = iuput_data["selected_time"]
        astro_id = all_astros[your_astro]
        today = datetime.now().strftime("%Y-%m-%d")
        reply_content = ''
        reply_message = f"【{time_selection}{your_astro}運勢】"

        # 今日
        if time_selection == "今日":
            url = f"https://astro.click108.com.tw/daily_{astro_id}.php?iAcDay={today}&iAstro={astro_id}&iType=0"

            response = requests.get(url)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            # 子標題
            overall = soup.find("span", {"class": "txt_green"}).text.strip()
            love = soup.find("span", {"class": "txt_pink"}).text.strip()
            career = soup.find("span", {"class": "txt_blue"}).text.strip()
            finance = soup.find("span", {"class": "txt_orange"}).text.strip()
            # 子標題內容
            all_content = soup.find(
                "div", {"class": "TODAY_CONTENT"})
            all_p = all_content.find_all('p')

            overall_content = all_p[1].text
            love_content = all_p[3].text
            career_content = all_p[-3].text
            finance_content = all_p[-1].text
            # reply_content += p.text.strip() + '\n'
            # reply_content = reply_content.rstrip('\n')

        # 明日
        elif time_selection == "明日":
            tomorrow = (datetime.now() + timedelta(days=1)
                        ).strftime("%Y-%m-%d")
            url = f"https://astro.click108.com.tw/daily_{astro_id}.php?iAcDay={tomorrow}&iAstro={astro_id}&iType=4"

            response = requests.get(url)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            overall = soup.find("span", {"class": "txt_green"}).text.strip()
            love = soup.find("span", {"class": "txt_pink"}).text.strip()
            career = soup.find("span", {"class": "txt_blue"}).text.strip()
            finance = soup.find("span", {"class": "txt_orange"}).text.strip()
            # 子標題內容
            all_content = soup.find(
                "div", {"class": "TODAY_CONTENT"})
            all_p = all_content.find_all('p')

            overall_content = all_p[1].text
            love_content = all_p[3].text
            career_content = all_p[-3].text
            finance_content = all_p[-1].text
            # all_content = soup.find(
            #     "div", {"class": "TODAY_CONTENT"})
            # for p in all_content.find_all('p'):
            #     reply_content += p.text.strip() + '\n'
            # reply_content = reply_content.rstrip('\n')

        # 本周
        elif time_selection == "本周":
            url = f"https://astro.click108.com.tw/weekly_{astro_id}.php?iAcDay={today}&iAstro={astro_id}&iType=1"

            response = requests.get(url)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            overall = soup.find("span", {"class": "txt_green"}).text.strip()
            love = soup.find("span", {"class": "txt_pink"}).text.strip()
            career = soup.find("span", {"class": "txt_blue"}).text.strip()
            finance = soup.find("span", {"class": "txt_orange"}).text.strip()
            # 子標題內容
            all_content = soup.find(
                "div", {"class": "TODAY_CONTENT"})
            all_p = all_content.find_all('p')

            overall_content = all_p[1].text
            love_content = all_p[3].text
            career_content = all_p[-3].text
            finance_content = all_p[-1].text
            # all_content = soup.find(
            #     "div", {"class": "TODAY_CONTENT"})
            # for p in all_content.find_all('p'):
            #     reply_content += p.text.strip() + '\n'
            # reply_content = reply_content.rstrip('\n')

        # 本月
        elif time_selection == "本月":
            url = f"https://astro.click108.com.tw/monthly_{astro_id}.php?iAcDay={today}&iAstro={astro_id}&iType=2"

            response = requests.get(url)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            overall = soup.find("span", {"class": "txt_green"}).text.strip()
            love = soup.find("span", {"class": "txt_pink"}).text.strip()
            career = soup.find("span", {"class": "txt_blue"}).text.strip()
            finance = soup.find("span", {"class": "txt_orange"}).text.strip()
            # 子標題內容
            all_content = soup.find(
                "div", {"class": "TODAY_CONTENT"})
            all_p = all_content.find_all('p')
            overall_content = all_p[1].text
            love_tmp = all_p[4:6]
            love_content = ''
            for p in love_tmp:
                print(p.text)
                love_content += p.text + '\n'
            career_tmp = all_p[-4:-2]
            career_content = ''
            for i in career_tmp:
                print(i.text)
                career_content += i.text + '\n'
            finance_content = all_p[-1].text
            # all_content = soup.find(
            #     "div", {"class": "TODAY_CONTENT"})
            # for p in all_content.find_all('p'):
            #     reply_content += p.text.strip() + '\n'
            # reply_content = reply_content.rstrip('\n')

    # reply_message += f"{reply_content}"

    # message = {
    #     "type": "text",
    #     "text": reply_message
    # }

    message = {
        "type": "flex",
        "altText": "星座運勢結果",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": reply_message,
                        "weight": "bold",
                        "size": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": overall,
                                "size": "md",
                                "color": "#CC7DE6",
                                "weight": "bold",
                                "margin": "md",
                                "flex": 0,
                                "wrap": True
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": overall_content,
                                "size": "sm",
                                "color": "#3B3B3B",
                                "margin": "md",
                                "flex": 0,
                                "wrap": True
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": love,
                                "size": "md",
                                "color": "#CC7DE6",
                                "weight": "bold",
                                "margin": "md",
                                "flex": 0,
                                "wrap": True
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": love_content.rstrip('\n'),
                                "size": "sm",
                                "color": "#3B3B3B",
                                "margin": "md",
                                "flex": 0,
                                "wrap": True
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": career,
                                "size": "md",
                                "color": "#CC7DE6",
                                "weight": "bold",
                                "margin": "md",
                                "flex": 0,
                                "wrap": True
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": career_content.rstrip('\n'),
                                "size": "sm",
                                "color": "#262626",
                                "margin": "md",
                                "flex": 0,
                                "wrap": True
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": finance,
                                "size": "md",
                                "color": "#CC7DE6",
                                "weight": "bold",
                                "margin": "md",
                                "flex": 0,
                                "wrap": True
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": finance_content,
                                "size": "sm",
                                "color": "#262626",
                                "margin": "md",
                                "flex": 0,
                                "wrap": True
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "資料來源：科技紫微網",
                                "size": "sm",
                                "color": "#999999",
                                "margin": "md",
                                "flex": 0,
                                "wrap": True
                            }
                        ]
                    },

                ]
            }
        }
    }

    return message


# ========================================================


def getNameEmojiMessage():
    lookUpStr = string.ascii_uppercase + string.ascii_lowercase
    productId = "5ac21a8c040ab15980c9b43f"
    name = "Harvey"
    message = dict()
    message['type'] = "text"
    message['text'] = "$" * len(name)
    emojis = list()
    for i, c in enumerate(name):
        emojis.append({
            "index": i,
            "productId": productId,
            "emojiId": f"{lookUpStr.index(c)+ 1}".zfill(3)
        })
    message['emojis'] = emojis
    return message


def getCarouselMessage(data):
    message = {
        "type": "template",
        "altText": "this is a image carousel template",
        "template": {
            "type": "image_carousel",
            "columns": [
              {
                "imageUrl": F"{end_point}/static/taipei_101.jpeg",
                "action": {
                    "type": "postback",
                    "label": "台北101",
                    "data": json.dumps(data)
                }
              },
                {
                  "imageUrl": F"{end_point}/static/02_shan.jpg",
                  "action": {
                      "type": "postback",
                      "label": "象山步道",
                      "data": json.dumps(data)
                  }
              },
                {
                    "imageUrl": F"{end_point}/static/03_yuanshan.jpg",
                    "action": {
                        "type": "postback",
                        "label": "圓山飯店",
                        "data": json.dumps(data)
                    }
              },
                {
                  "imageUrl": F"{end_point}/static/04_taipeizoo.jpg",
                    "action": {
                        "type": "postback",
                        "label": "台北動物園",
                        "data": json.dumps(data)
                    }
              },
                {
                  "imageUrl": F"{end_point}/static/05_nightmarket.jpg",
                  "action": {
                      "type": "postback",
                      "label": "饒河夜市",
                      "data": json.dumps(data)
                  }
              }
            ]
        }
    }
    return message


def getCallCarMessage(data):
    message = {
        "type": "template",
        "altText": "this is a template",
        "template": {
            "type": "buttons",
            "text": f"請選擇至 {data['title']} 預約叫車時間",
            "actions": [
              {
                  "type": "datetimepicker",
                  "label": "預約",
                  "data": json.dumps(data),
                  "mode": "datetime"
              }
            ]
        }
    }
    return message


def getLocationConfirmMessage(title, latitude, longitude):
    data = {"latitude": latitude, "longitude": longitude,
            "title": title, "action": "get_near"}
    message = {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
                "type": "confirm",
                "text": f"是否要搜尋 {title} 附近的景點？",
                "actions": [
                    {
                        "type": "postback",
                        "label": "是",
                        "data": json.dumps(data),
                        "displayText": "是",
                    },
                    {
                        "type": "message",
                        "label": "否",
                        "text": "否"
                    }
                ]
        }
    }
    return message


def getPlayStickerMessage():
    message = {
        "type": "sticker",
        "packageId": "446",
        "stickerId": "1988"
    }
    return message


def getTaipei101LocationMessage():
    message = {
        "type": "location",
        "title": "Taipei 101",
        "address": "台北市信義區信義路五段7號89樓",
        "latitude": 25.034804599999998,
        "longitude": 121.5655868
    }
    return message


def getMRTVideoMessage(originalContentUrl=F"{end_point}/static/taipei_101_video.mp4"):
    message = {
        "type": "video",
        "originalContentUrl": F"{end_point}/static/taipei_101_video.mp4",
        "previewImageUrl": F"{end_point}/static/taipei_101.jpeg",
        "trackingId": "track-id"
    }
    return message


def getMRTSoundMessage():
    message = dict()
    message["type"] = "audio"
    message["originalContentUrl"] = F"{end_point}/static/mrt_sound.m4a"
    import audioread
    with audioread.audio_open('static/mrt_sound.m4a') as f:
        # totalsec contains the length in float
        totalsec = f.duration
    message["duration"] = totalsec * 1000
    return message


def getTaipei101ImageMessage(originalContentUrl=F"{end_point}/static/taipei_101.jpeg"):

    return getImageMessage(originalContentUrl)


def getImageMessage(originalContentUrl):
    message = {
        "type": "image",
        "originalContentUrl": originalContentUrl,
        "previewImageUrl": originalContentUrl
    }
    return message


def replyMessage(payload):
    response = requests.post(
        "https://api.line.me/v2/bot/message/reply", headers=HEADER, json=payload)
    print(response.text)
    print('payload =', payload)
    return 'OK'


def pushMessage(payload):
    response = requests.post(
        "https://api.line.me/v2/bot/message/push", headers=HEADER, json=payload)
    print(response.text)
    return 'OK'


def getTotalSentMessageCount():
    response = {}
    return 0


def getTodayCovid19Message():
    response = requests.get(
        "https://covid-19.nchc.org.tw/api/covid19?CK=covid-19@nchc.org.tw&querydata=3001&limited=BGD", headers=HEADER)
    data = response.json()[0]
    date = data['a04']
    total_count = data['a05']
    count = data['a06']
    return F"日期：{date}, 人數：{count}, 確診總人數：{total_count}"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload_file', methods=['POST'])
def upload_file():
    payload = dict()
    if request.method == 'POST':
        file = request.files['file']
        print("json:", request.json)
        form = request.form
        age = form['age']
        gender = ("男" if form['gender'] == "M" else "女") + "性"
        if file:
            filename = file.filename
            img_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(img_path)
            print(img_path)
            payload["to"] = my_line_id
            payload["messages"] = [getImageMessage(F"{end_point}/{img_path}"),
                                   {
                "type": "text",
                "text": F"年紀：{age}\n性別：{gender}"
            }
            ]
            pushMessage(payload)
    return 'OK'


@app.route('/line_login', methods=['GET'])
def line_login():
    if request.method == 'GET':
        code = request.args.get("code", None)
        state = request.args.get("state", None)

        if code and state:
            HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
            url = "https://api.line.me/oauth2/v2.1/token"
            FormData = {"grant_type": 'authorization_code', "code": code, "redirect_uri": F"{end_point}/line_login",
                        "client_id": line_login_id, "client_secret": line_login_secret}
            data = parse.urlencode(FormData)
            content = requests.post(url=url, headers=HEADERS, data=data).text
            content = json.loads(content)
            url = "https://api.line.me/v2/profile"
            HEADERS = {
                'Authorization': content["token_type"]+" "+content["access_token"]}
            content = requests.get(url=url, headers=HEADERS).text
            content = json.loads(content)
            name = content["displayName"]
            userID = content["userId"]
            pictureURL = content["pictureUrl"]
            statusMessage = content["statusMessage"]
            print(content)
            return render_template('profile.html', name=name, pictureURL=pictureURL, userID=userID, statusMessage=statusMessage)
        else:
            return render_template('login.html', client_id=line_login_id,
                                   end_point=end_point)


if __name__ == "__main__":
    app.debug = True
    app.run()
