import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

import datetime as dt

import os

# (1) Google Spread Sheetsにアクセス
def connect_gspread(jsonf,key,index):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(jsonf, scope)
    gc = gspread.authorize(credentials)
    SPREADSHEET_KEY = key
    wb = gc.open_by_key(SPREADSHEET_KEY)
    worksheet = wb.get_worksheet(index)
    return worksheet

def return_ws(index):
    jsonf = os.getenv('JSONF')
    spread_sheet_key = os.getenv('SPREAD_SHEET_KEY')
    ws = connect_gspread(jsonf,spread_sheet_key,index)
    return ws

def change_day(day):
    if day == "Sun":
        day = "(日)"
    elif day == "Mon":
        day = "(月)"
    elif day == "Tue":
        day = "(火)"
    elif day == "Wed":
        day = "(水)"
    elif day == "Thu":
        day = "(木)"
    elif day == "Fri":
        day = "(金)"
    elif day == "Sat":
        day = "(土)"
    return day

# homework_info.csvを作成する
def make_homework_info():
    ws = return_ws(0)
    # すべての値を取得
    values = ws.get_all_values()
    # 行数を取得
    all_row = len(values)
    push_text = ""
    for i in range(1,all_row):
        rows = values[i]
        year,month,date = map(int,rows[5].split("/"))
        day = change_day(dt.date(year,month,date).strftime("%a"))
        push_text += (f"{rows[1]},{rows[2]},{rows[3]},{rows[4]},{month},{date},{day}\n")
    with open("homework_info.csv", "w", encoding="utf-8") as f:
        f.write(push_text)

# spreadsheetから教科名と番号が一致する場所を消す
def delete_homework(subject,num):
    ws = return_ws(0)
    values = ws.get_all_values()
    all_row = len(values)
    flag = False
    for i in range(1,all_row-1):
        rows = values[i]
        if subject == rows[1] and int(num) == int(rows[3]) or flag:
            flag = True
            ws.update(f"A{i+1}:L{i+1}",[values[i+1]])
    ws.delete_row(all_row)

# reminder_time.csv を spreadsheet にも追加する
def set_reminder():
    ws = return_ws(1)
    values = ws.get_all_values()
    with open("reminder_time.csv" , "r" , encoding="utf-8") as f:
        lines = f.readlines()
    push_text = []
    for line in lines:
        user_id,days,time = line.rstrip().split(",")
        push_text.append([user_id,days,time])
    ws.update(f"A1:C{len(push_text)}",push_text)

def delete_reminder(userid):
    ws = return_ws(1)
    values = ws.get_all_values()
    all_row = len(values)
    flag = False
    print(values,all_row)
    for i in range(all_row-1):
        rows = values[i]
        if userid == rows[0] or flag:
            flag = True
            ws.update(f"A{i+1}:L{i+1}",[values[i+1]])
    ws.delete_row(all_row)