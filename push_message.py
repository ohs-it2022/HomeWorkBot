from linebot import LineBotApi
from linebot.models import TextSendMessage
import datetime
import time

import app
import edit_spreadsheet
import os

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

subject_list = ["CS12","WB12","PY12","CT12","JS11","DB11","IH11","SL11","FX11","SF11"]

def main():
    # UTCの時間を取得
    time_now_utc = datetime.datetime.now(datetime.timezone.utc)
    time_dt_ja = datetime.timedelta(hours=9)
    # 日本の時間に合わせる
    time_now_ja = time_now_utc + time_dt_ja
    print(time_now_ja)

    with open("reminder_time.csv", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        user_id,push_days,push_times = line.rstrip().split(",")
        remind_list = []
        flag = False
        hw_info_list = app.list_from_hw_info()
        for subject,format,no,title,month,date,day in hw_info_list:
            days_remaining = app.calc_day(month,date)
            if (days_remaining == int(push_days)) and (time_now_ja.hour == int(push_times)) and (time_now_ja.minute == 0):
                remind_list.append(subject)
                flag = True
        if  flag:
            if push_days == "0":
                message = TextSendMessage(text=f"本日、{remind_list}の課題があります。")
            elif push_days == "1":
                message = TextSendMessage(text=f"明日、{remind_list}の課題があります。")
            else:
                message = TextSendMessage(text=f"{days_remaining}日後、{remind_list}の課題があります。")
            line_bot_api.push_message(user_id, messages=message)

if __name__ == "__main__":
    main()