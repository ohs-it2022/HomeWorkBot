from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
)
import datetime
import edit_spreadsheet
from dotenv import load_dotenv
load_dotenv()

import os

line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SEARCRET'))

groupId = os.getenv('GROUP_ID')

app = Flask(__name__)

@app.route("/")
def test():
    return "ok"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# -----------------------------------

# 入力値を文字列に変換
def change_str(m,d):
    time_now_utc = datetime.datetime.now(datetime.timezone.utc)
    time_dt_ja = datetime.timedelta(hours=9)
    today = time_now_utc + time_dt_ja
    n_year = today.year
    n_month = today.month
    n_day = today.day

    if int(m) >= n_month:
        pass
    elif int(m) <= 3:
        n_year += 1
    str_date = str(n_year) + "-" + str(m) + "-" + str(d)
    return str_date

# 入力値を日付型に変換
def change_date(m,d):
    str_date = change_str(m,d)
    dead_line = datetime.datetime.strptime(str_date, "%Y-%m-%d")
    return dead_line

# 残り日数計算
def calc_day(m,d):
    print("calc start")
    time_now_utc = datetime.datetime.now(datetime.timezone.utc)
    print("time_now_utc :", time_now_utc)
    time_dt_ja = datetime.timedelta(hours=9)
    print("time_dt_ja :", time_dt_ja)
    today = time_now_utc + time_dt_ja
    print("today :", today)
    tstr,ano = str(today).split(".")
    # tstr = "2022-11-28 09:52:11"
    print("tstr :", tstr)
    time_now_ja = datetime.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S')
    print("today1 :", time_now_ja)
    dead_line = change_date(m,d)
    print("deadline :", dead_line)
    work = str(dead_line - time_now_ja)
    if "day" in work:
        days_remaining,ano = work.split("day")
    else:
        days_remaining = 0
    print("c")
    return int(days_remaining) + 1

# 教科名を揃える
def arrange(subject):
    if subject in subject_list_11:
        subject = subject + "11"
    elif subject in subject_list_12:
        subject = subject + "12"
    return subject

# 日付の論理チェック
def check_day(m,d):
    flag = True
    month_list = [1,2,3,4,5,6,7,8,9,10,11,12]
    if (m not in month_list) or d < 1 or d > 31:
        flag = False
    else:
        if (m in [2,4,6,9,11]) and d > 30:
            flag = False
        if m == 2 and d > 28:
            flag = False
    return flag

# 時間の論理チェック
def check_time(tell_time):
    flag = True
    if tell_time < 0 or tell_time >= 24:
        flag = False
    return flag

# 課題情報ファイルをリストで返す
def list_from_hw_info():
    hw_info_list = []
    lines = read_file("homework_info.csv")
    for line in lines:
        columns = line.rstrip().split(',')
        hw_info_list.append(columns)
    return hw_info_list

# 課題一覧用関数
def see_homework():
    try:
        hw_info_list = list_from_hw_info()
        if len(hw_info_list) == 0:
            rep = "現在登録されてる課題はありません！"
        else:
            rep = "<<課題一覧>>"
            for subject,format,no,title,month,date,day in hw_info_list:
                row = f"{subject} : {month}/{date} {day}"
                rep = f"{rep}\n{row}"
        reply_message = rep
    except:
        reply_message = "入力エラー"
    return reply_message

# 課題消去用関数
def delete_homework(text):
    try:
        cmd,subject,num = text.split()
        subject = arrange(subject)
        hw_info_list = list_from_hw_info()
        flag = True
        for line in hw_info_list:
            if (subject == line[0]) and (int(num) == int(line[2])) and flag:
                flag = False
                edit_spreadsheet.delete_homework(subject,num)
                edit_spreadsheet.make_homework_info()
        if flag:
            reply_message = f"{subject}の課題No.{num}は登録されていません！"
        else:
            reply_message = f"{subject}の課題No.{num}を削除しました。"
    except:
        reply_message = "入力エラー"
    return reply_message

# 教科名ごとの課題情報を返す
def subject_name(text,today_month_day):
    try:
        hw_info_list = list_from_hw_info()
        text = arrange(text)
        flag = True
        for subject,format,no,title,month,date,day in hw_info_list:
            print(month,date)
            if subject == text:
                if flag:
                    reply_message = "課題があります。\n"
                    flag = False
                else:
                    reply_message += "\n\n"
                if f"{month}/{date}" == today_month_day:
                    print("true")
                    reply_message += f"締め切り日 : 今日"
                else:
                    print("else")
                    limitday = calc_day(month,date)
                    print(limitday)
                    if limitday == 1:
                        reply_message += f"締め切り日 : 明日"
                    elif limitday == 2:
                        reply_message += f"締め切り日 : 明後日"
                    else:
                        reply_message += f"締め切り日まで残り{limitday}日"
                reply_message += f"\n形式 : {format}\n課題No.{no} \n主題 : {title}"
        if flag:
            reply_message = "課題は登録されていません。" 
    except:
        reply_message = "入力エラー"
    return reply_message

# ファイルを読み込む
def read_file(file_name):
    with open(file_name, mode="r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines

# リマインダー設定用関数
def set_reminder_time(text,event):
    try:
        cmd,tell_days,tell_time = text.split()
        tell_days,tell_time = map(int,(tell_days,tell_time))
        check_t = check_time(tell_time)
        if check_t:
            userid = event.source.user_id
            find_tf = False
            lines = read_file("reminder_time.csv")
            new_text = ""
            for line in lines:
                if userid in line:
                    find_tf = True
                    new_text += f"{userid},{tell_days},{tell_time}\n"
                else:
                    new_text += line
            if find_tf:
                with open("reminder_time.csv", mode="w", encoding="utf-8") as f:
                    f.write(new_text)
            else:
                with open("reminder_time.csv", mode="a", encoding="utf-8") as f:
                    print(f"{userid},{tell_days},{tell_time}",file=f)
            if tell_days == 0:
                day = "当日"
            elif tell_days == 1:
                day = "前日"
            else:
                day = f"{tell_days}日前"
            reply_message = f"{day}の{tell_time}時に通知します！"
            edit_spreadsheet.set_reminder()
        else:
            reply_message = f"{tell_time}時は存在しません"
    except:
        reply_message = "入力エラー"
    return reply_message

def delete_reminder(event):
    userid = event.source.user_id
    lines = read_file("reminder_time.csv")
    find_tf = False
    new_text = ""
    for line in lines:
        if userid in line:
            find_tf = True
        else:
            new_text += line
    if find_tf:
        with open("reminder_time.csv", mode="w", encoding="utf-8") as f:
            f.write(new_text)
        reply_message = "通知の設定を取り消しました"
        edit_spreadsheet.delete_reminder(userid)
    else:
        reply_message = "通知設定がされていません"
    
    return reply_message


# -----------------------------------

subject_list = ["CS12","WB12","PY12","CT12","JS11","DB11","IH11","SL11","FX11","SF11"]
subject_list_11 = ["JS","DB","IH","SL","FX","SF"]
subject_list_12 = ["CS","WB","PY","CT"]

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    time_now_utc = datetime.datetime.now(datetime.timezone.utc)
    time_dt_ja = datetime.timedelta(hours=9)
    today = time_now_utc + time_dt_ja
    today_month_day = f"{today.month}/{today.day}"
    flag = False
    t = event.message.text
    text = t.upper() # 大文字に変換

    if (text == "課題一覧") or (text == "課題確認") or (text == "-S") or (text == "ーＳ"):
        edit_spreadsheet.make_homework_info()
        reply_message = see_homework()
    elif ("-D" in text):
        try:
            if event.source.group_id == groupId:
                reply_message = delete_homework(text)
        except:
            reply_message = "削除コマンドはグループ専用です"
    elif (text in subject_list) or (text in subject_list_11) or (text in subject_list_12):
        edit_spreadsheet.make_homework_info()
        reply_message = subject_name(text,today_month_day)
    elif "SET" == text:
        reply_message = "set 〇 △と入力してください。\n〇＝何日前(当日は0,前日は1,...)\n△＝何時(0時は0,1時は1,...)"
    elif "SET DEL" == text:
        reply_message = delete_reminder(event)
    elif "SET" in text:
        reply_message = set_reminder_time(text,event)
    elif ("-FORM" == text) or ("フォーム" == text) or ("FORM" == text):
        try:
            if event.source.group_id == groupId:
                flag = True
                reply_message = "https://forms.gle/sd5nbU3jvbxTQ4GcA"
        except:
            reply_message = f"フォーム送信コマンドはグループ専用です"
    elif "マニュアル" == text or "-M" == text:
        url = "https://curious-empanada-671453.netlify.app/manual_ver1.jpg"
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url=url,
                preview_image_url=url,
                ))
        exit()
    else:
        reply_message = f"{t}は定義されていません"

    try:
        if event.source.group_id == groupId:
            if flag:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(reply_message))
    except:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(reply_message))
            

if __name__ == "__main__":
    app.run()