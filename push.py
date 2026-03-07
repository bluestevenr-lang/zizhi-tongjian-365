import requests
import hashlib
import hmac
import base64
import time
import os
from datetime import datetime, timezone, timedelta

WEBHOOK = os.environ.get('DINGTALK_WEBHOOK', '')
SECRET = os.environ.get('DINGTALK_SECRET', '')

BJT = timezone(timedelta(hours=8))
now = datetime.now(BJT)
hour = now.hour

START_DATE = datetime(2026, 3, 8, tzinfo=BJT)
today = datetime(now.year, now.month, now.day, tzinfo=BJT)
day_num = (today - START_DATE).days + 1
day_num = max(1, min(365, day_num))

time_pct = round(day_num / 365 * 100, 1)
total_vols = 294
current_vol = max(1, min(total_vols, round(day_num / 365 * total_vols)))
book_pct = round(current_vol / total_vols * 100, 1)

CONTENT = {
    1: {
        "era": "周纪一 威烈王二十三年",
        "original": "威烈王二十三年，初命晋大夫魏斯、赵籍、韩虔为诸侯。臣光曰：臣闻天子之职莫大于礼，礼莫大于分，分莫大于名。",
        "translation": "周威烈王二十三年，天子正式册封晋国大夫魏斯、赵籍、韩虔为诸侯。司马光说：天子最重要的职责是维护礼制，礼制的核心在于等级名分，名分一旦崩坏，天下必乱。",
        "person": "魏文侯魏斯，三家分晋核心人物。礼贤下士，重用李悝变法，使魏成为战国初期最强诸侯。与人期雨雪不废，以诚信治国流传千古。",
        "analysis": "司马光以三家分晋开篇，周天子承认既成事实，正是礼崩乐坏的象征。规则的破坏，往往从第一次例外开始。",
        "work_insight": "团队规则出现特例时，公平感立刻崩塌。管理者对破坏规则的第一次妥协，往往比规则本身破坏力更大。",
        "eq_insight": "魏文侯雨夜赴约，不因地位高贵而失信。真正的情商，是在无人监督时依然兑现承诺。",
        "study_insight": "读史要见第一个转折点，任何大变局都有其初命，找到那个起点才能真正理解历史走向。",
        "quote": "天子之职莫大于礼，礼莫大于分，分莫大于名。",
        "tomorrow": "魏文侯变法李悝新政，战国第一次变法如何让魏国崛起",
    },
    2: {
        "era": "周纪一 魏文侯时期",
        "original": "魏文侯以卜子夏、田子方为师，每过段干木之庐必式。四方贤士多归之。",
        "translation": "魏文侯拜子夏、田子方为老师，每次经过段干木的住所必定在车上欠身行礼。四方贤士因此纷纷归附他。",
        "person": "李悝，魏国著名法家，主持李悝变法，编著法经，推行尽地力之教，使魏国迅速富强，成为战国变法先驱。",
        "analysis": "魏文侯尊师重道并非作秀，而是真正认识到人才是国家最重要的资源。他的礼贤行为创造了强大的人才磁场。",
        "work_insight": "领导者对人才的态度决定团队天花板。真正的尊重不是嘴上说说，而是用行动让人才感受到被重视。",
        "eq_insight": "放低身段不是软弱，而是一种战略智慧。魏文侯贵为诸侯却向士人行礼，这种情商让他获得了无数人的效忠。",
        "study_insight": "学习要找最好的老师。魏文侯同时拜多位大师为师，博采众长，这种学习策略值得借鉴。",
        "quote": "四方贤士多归之。",
        "tomorrow": "吴起练兵魏武卒，战国最强步兵如何炼成",
    },
    3: {
        "era": "周纪一 吴起在魏",
        "original": "吴起为将，与士卒最下者同衣食，卧不设席，行不骑乘，亲裹赢粮，与士卒分劳苦。",
        "translation": "吴起担任将领，与最下层的士卒穿一样的衣服吃一样的饭食，睡觉不铺席子，行军不骑马，亲自背负军粮，与士卒共同承担劳苦。",
        "person": "吴起，战国时代最杰出的军事家之一，历仕鲁魏楚三国。在魏训练魏武卒，打造战国最强步兵。著有吴子兵法，与孙子并称孙吴。",
        "analysis": "吴起的管理哲学：身先士卒，同甘共苦。他训练的魏武卒创下大战七十二全胜六十四的辉煌战绩。",
        "work_insight": "最好的管理不是发号施令，而是以身作则。当领导者愿意同甘共苦，团队的执行力将成倍提升。",
        "eq_insight": "高情商的领导者懂得用具体行动而非空洞言辞来建立信任。",
        "study_insight": "任何技能的精进都需要与最优秀的人同频，通过设立高标准严训练来实现。",
        "quote": "与士卒分劳苦。",
        "tomorrow": "商鞅变法秦国崛起，改变中国历史走向的变法",
    },
}

def get_content(day):
    if day in CONTENT:
        return CONTENT[day]
    idx = ((day - 1) % len(CONTENT)) + 1
    return CONTENT[idx]

def sign():
    timestamp = str(round(time.time() * 1000))
    string_to_sign = timestamp + "\n" + SECRET
    hmac_code = hmac.new(SECRET.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    sign_val = base64.b64encode(hmac_code).decode('utf-8')
    import urllib.parse
    return timestamp, urllib.parse.quote_plus(sign_val)

def send(msg):
    timestamp, sign_val = sign()
    url = WEBHOOK + "&timestamp=" + timestamp + "&sign=" + sign_val
    data = {"msgtype": "markdown", "markdown": {"title": msg["title"], "text": msg["text"]}}
    resp = requests.post(url, json=data, timeout=10)
    print("推送结果:", resp.json())

c = get_content(day_num)
date_str = now.strftime("%Y.%m.%d")
day_str = "第" + str(day_num) + "天/365天"
tb = chr(9608) * int(time_pct / 5) + chr(9617) * (20 - int(time_pct / 5))
bb = chr(9608) * int(book_pct / 5) + chr(9617) * (20 - int(book_pct / 5))

if hour < 12:
    msg = {
        "title": "资治通鉴学习 " + day_str + " 进度" + str(time_pct) + "%",
        "text": "## 资治通鉴学习 晨读\n> " + date_str + " " + day_str + " " + c['era'] + "\n\n**时间进度** " + str(time_pct) + "%\n\n" + tb + " " + str(day_num) + "/365天\n\n**书籍进度** " + str(book_pct) + "%\n\n" + bb + " 卷" + str(current_vol) + "/294卷\n\n---\n### 今日原文\n> " + c['original'] + "\n\n### 白话译文\n" + c['translation'] + "\n\n---\n### 今日人物\n" + c['person'] + "\n\n晚上21点推送章节解析"
    }
elif hour < 22:
    msg = {
        "title": "资治通鉴学习 " + day_str + " 章节解析",
        "text": "## 资治通鉴学习 晚读\n> " + date_str + " " + day_str + " " + c['era'] + "\n\n**时间进度** " + str(time_pct) + "%\n\n" + tb + " " + str(day_num) + "/365天\n\n**书籍进度** " + str(book_pct) + "%\n\n" + bb + " 卷" + str(current_vol) + "/294卷\n\n---\n### 章节解析\n" + c['analysis'] + "\n\n---\n### 引申思考\n\n**职场启示**\n" + c['work_insight'] + "\n\n**情商修炼**\n" + c['eq_insight'] + "\n\n**学习方法**\n" + c['study_insight'] + "\n\n晚上22点推送今日总结"
    }
else:
    msg = {
        "title": "资治通鉴学习 " + day_str + " 今日总结",
        "text": "## 资治通鉴学习 夜总结\n> " + date_str + " " + day_str + " " + c['era'] + "\n\n**时间进度** " + str(time_pct) + "% 还剩" + str(365-day_num) + "天\n\n" + tb + " " + str(day_num) + "/365天\n\n**书籍进度** " + str(book_pct) + "% 还剩" + str(total_vols-current_vol) + "卷\n\n" + bb + " 卷" + str(current_vol) + "/294卷\n\n---\n### 今日总结\n- 今日篇章：" + c['era'] + "\n- 核心思想：" + c['analysis'][:40] + "...\n\n---\n### 今日金句\n> " + c['quote'] + "\n> 司马光 资治通鉴\n\n---\n### 明日预告\n" + c['tomorrow'] + "\n\n已连续学习第" + str(day_num) + "天，继续加油！"
    }

send(msg)
