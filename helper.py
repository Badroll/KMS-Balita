import json
from flask import jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from os import path
import random

import env


def composeReply(status, message, payload = None, statuscode = 200):
    reply = {}
    reply["SENDER"] = "KMS API"
    reply["STATUS"] = status
    reply["MESSAGE"] = message
    reply["PAYLOAD"] = payload
    resp = jsonify(reply)
    resp.headers.add("Access-Control-Allow-Origin", "*")
    resp.status_code = statuscode
    return resp


def allowed_file(filename):
    IMAGE_ALLOWED_EXTENSION = ["png", "jpg", "jpeg"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in IMAGE_ALLOWED_EXTENSION


def saveFile(file):
    try:
        filename = str(get_local_time()).replace(":", "-") + secure_filename(file.filename)
        basedir = path.abspath(path.dirname(__file__))
        file.save(path.join(basedir, "uploads", filename))
        return filename
    except TypeError as error : return False


def db_raw(qry, host=env.dbHost, user=env.dbUser, passwd=env.dbPassword, database=env.dbDatabase, string_datetime=True):
    import pymysql

    rStatus = True
    rMessage = "ERROR"

    db = pymysql.connect(host=host, user=user, passwd=passwd, database=database)
    c = db.cursor()
    try:
        qry = f"{qry}"
        print(qry)
        c.execute(qry)
        json_data = []
        if qry.lstrip().lower().startswith("select"):
            data = c.fetchall()
            row_headers = [x[0] for x in c.description]
            for result in data:
                formatted_result = {}
                for i in range(len(row_headers)):
                    column_name = row_headers[i]
                    column_value = result[i]
                    if string_datetime:
                        if isinstance(column_value, datetime):
                            formatted_result[column_name] = column_value.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            formatted_result[column_name] = column_value
                json_data.append(formatted_result)

        rMessage = json_data
        db.commit()
        c.close()

    except Exception as e:
        rStatus = False
        rMessage = str(e)
        print("db_raw", str(e))
        c.close()

    return [rStatus, rMessage]


def db_insert(table, data):
    import pymysql

    rStatus = True
    rMessage = ""
    
    db = pymysql.connect(host=env.dbHost, user=env.dbUser, passwd=env.dbPassword, database=env.dbDatabase)
    c = db.cursor()
    try:
        columns = ",".join(data.keys())
        placeholders = ",".join(["%s" for _ in data.values()])
        values = tuple(data.values())

        qry = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        c.execute(qry, values)
        id = c.lastrowid
        rMessage = id
        db.commit()
        c.close()

    except Exception as e:
        rStatus = False
        rMessage = str(e)
        print("db_insert", str(e))
        c.close()

    return [rStatus, rMessage]


def db_update(table, data, where_clause):
    import pymysql

    rStatus = True
    rMessage = ""
    
    db = pymysql.connect(host=env.dbHost, user=env.dbUser, passwd=env.dbPassword, database=env.dbDatabase)
    c = db.cursor()
    try:
        set_values = ",".join([f"{column} = %s" for column in data.keys()])
        values = tuple(data.values())

        qry = f"UPDATE {table} SET {set_values} WHERE 1 AND ({where_clause})"
        c.execute(qry, values)
        db.commit()
        c.close()

    except Exception as e:
        rStatus = False
        rMessage = str(e)
        print("db_update", str(e))
        c.close()

    return [rStatus, rMessage]


def db_delete(table, where_clause):
    import pymysql

    rStatus = True
    rMessage = ""

    db = pymysql.connect(host=env.dbHost, user=env.dbUser, passwd=env.dbPassword, database=env.dbDatabase)
    c = db.cursor()
    try:
        qry = f"DELETE FROM {table} WHERE 1 AND ({where_clause})"
        c.execute(qry)
        db.commit()
        c.close()

    except Exception as e:
        rStatus = False
        rMessage = str(e)
        print("db_delete", str(e))
        c.close()

    return [rStatus, rMessage]


def sqlresGet(cursor):
    data = cursor.fetchall()
    row_headers = [x[0] for x in cursor.description]
    json_data = []
    for result in data:
        json_data.append(dict(zip(row_headers, result)))
    
    return json_data


def randomString(length, str):
    result = ''.join((random.choice(str)) for x in range(length))
    return result


def bubbleSort(arr):
	n = len(arr)
	swapped = False
	for i in range(n-1):
		for j in range(0, n-i-1):
			if arr[j] > arr[j + 1]:
				swapped = True
				arr[j], arr[j + 1] = arr[j + 1], arr[j]
		if not swapped:
			print("ok")
	return arr


def send_telegram(msg, chat_id = env.tele_chat_id_bdmsth_logger_pakdhe):
    import requests
    message = msg
    url = f"https://api.telegram.org/bot{env.telebot_token}/sendMessage?chat_id={chat_id}&text={message}"
    r = requests.get(url).json()

def send_telegram_photo(file, chat_id = env.tele_chat_id_bdmsth_logger_pakdhe):
    import requests
    path_to_image = file
    url = f"https://api.telegram.org/bot{env.telebot_token}/sendPhoto"
    data = {
        "chat_id": chat_id,
    }
    with open(path_to_image, "rb") as image_file:
        files = {"photo": image_file}
        response = requests.post(url, data=data, files=files)
    r = response.json()


def get_setting(id):
    import pymysql

    setting = db_raw(f"SELECT * FROM _setting WHERE S_ID = '{id}'")
    if setting[0] == False or len(setting[1]) == 0:
        return "-"
    else:
        return setting[1]["S_VALUE"]


def send_wa_multipleSendText(phone, message, account=1):
    import requests
    url = "https://kudus.wablas.com/api/v2/send-message"
    headers = {
        "Content-Type": "application/json",
        "Authorization": env.wabot[f"wabot_{account}_token"],
    }
    data = {
        "data": [
            {
                "phone": phone,
                "message": message
            }
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    success = False
    if response.status_code == 200:
        success = True

    log_curl(get_local_time().strftime('%Y-%m-%d %H:%M:%S'), url, "Wablas multipleSendText", "POST", json.dumps(headers), json.dumps(data), response.text)
    
    return [success, str(response.text)]


def send_wa_multipleSendImage(phone, caption, url, account=1):
    import requests
    url = "https://kudus.wablas.com/api/v2/send-image"
    headers = {
        "Content-Type": "application/json",
        "Authorization": env.wabot[f"wabot_{account}_token"],
    }
    data = {
        "data": [
            {
                "phone": phone,
                "image": url,
                "caption": caption
            }
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    success = False
    if response.status_code == 200:
        success = True

    log_curl(get_local_time().strftime('%Y-%m-%d %H:%M:%S'), url, "Wablas multipleSendImage", "POST", json.dumps(headers), json.dumps(data), response.text)
    
    return [success, str(response.text)]

    
def log_curl(datetime, url, name, method, header, data, reponse):
    import pymysql

    mydb = pymysql.connect(host=env.dbHost, user=env.dbUser, passwd=env.dbPassword, database=env.dbDatabase)
    cursor = mydb.cursor()
    query = """INSERT INTO request (REQUEST_DATETIME, REQUEST_URL, REQUEST_NAME, REQUEST_METHOD, REQUEST_HEADER, REQUEST_DATA, REQUEST_RESPONSE)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """
    values = (datetime, url, name, method, header, data, reponse)
    cursor.execute(query, values)
    mydb.commit()
    cursor.close()


def generate_token():
    import secrets
    return secrets.token_hex(16)


def create_hash(r_text):
    import hashlib

    text = r_text + env.sha256_addon_key

    print("create_hash", text)
    
    # Pilih algoritma hash yang aman, seperti SHA-256
    sha256 = hashlib.sha256()

    # Konversi teks menjadi byte (encoding utf-8 digunakan di sini)
    text_bytes = text.encode('utf-8')

    # Update objek hash dengan byte teks
    sha256.update(text_bytes)

    # Dapatkan hash dalam bentuk hexadecimal
    hashed_text = sha256.hexdigest()

    return hashed_text

# Fungsi untuk memeriksa apakah teks cocok dengan hash
def check_hash(r_text, hashed_text):
    text = r_text
    print("check_hash", text)
    # Membuat hash baru dari teks yang sama
    new_hashed_text = create_hash(text)

    # Membandingkan hash yang baru dibuat dengan hash yang diberikan
    return new_hashed_text == hashed_text


def get_reference_info(id):
    r = db_raw(f"""
        SELECT * FROM _reference WHERE R_ID = '{id}'
    """)
    print(r)
    if r[0] and len(r[1]) > 0:
        return r[1][0]
    return "-"


def col_to_num_excel(kolom):
    angka = 0
    for i, huruf in enumerate(reversed(kolom)):
        angka += (ord(huruf) - ord('A') + 1) * (26 ** i)
    return angka

def get_cells_in_range(sheet, range_str):
    range_str = range_str.split(":")
    column_start = col_to_num_excel(range_str[0].split("-")[0])
    row_start = int(range_str[0].split("-")[1])
    column_end = col_to_num_excel(range_str[1].split("-")[0])
    row_end = int(range_str[1].split("-")[1])
    r_cell = []
    for row in sheet.iter_rows(min_row=row_start, max_row=row_end, min_col=column_start, max_col=column_end):
        for cell in row:
            r_cell.append(cell)
    return r_cell


def tgl_indo(tgl, mode):
    if not tgl == None and tgl != "" and mode != "" and tgl != "0000-00-00" and tgl != "0000-00-00 00:00:00":
        t = tgl.split("-")
        bln = {
            "01": {"LONG": "Januari", "SHORT": "Jan"},
            "1": {"LONG": "Januari", "SHORT": "Jan"},
            "02": {"LONG": "Februari", "SHORT": "Feb"},
            "2": {"LONG": "Februari", "SHORT": "Feb"},
            "03": {"LONG": "Maret", "SHORT": "Mar"},
            "3": {"LONG": "Maret", "SHORT": "Mar"},
            "04": {"LONG": "April", "SHORT": "Apr"},
            "4": {"LONG": "April", "SHORT": "Apr"},
            "05": {"LONG": "Mei", "SHORT": "Mei"},
            "5": {"LONG": "Mei", "SHORT": "Mei"},
            "06": {"LONG": "Juni", "SHORT": "Jun"},
            "6": {"LONG": "Juni", "SHORT": "Jun"},
            "07": {"LONG": "Juli", "SHORT": "Jul"},
            "7": {"LONG": "Juli", "SHORT": "Jul"},
            "08": {"LONG": "Agustus", "SHORT": "Ags"},
            "8": {"LONG": "Agustus", "SHORT": "Ags"},
            "09": {"LONG": "September", "SHORT": "Sep"},
            "9": {"LONG": "September", "SHORT": "Sep"},
            "10": {"LONG": "Oktober", "SHORT": "Okt"},
            "11": {"LONG": "November", "SHORT": "Nov"},
            "12": {"LONG": "Desember", "SHORT": "Des"},
        }

        b = t[1]

        if ":" not in t[2]:  # tidak ada format waktu
            jam = ""
        else:
            j = t[2].split(" ")
            t[2] = j[0]
            jam = j[1]

        return f"{t[2]} {bln[b][mode]} {t[0]} {jam}"
    else:
        return "-"


def get_local_time():
    import pytz
    utc_time = datetime.utcnow()
    jakarta_timezone = pytz.timezone('Asia/Jakarta')
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(jakarta_timezone)
    return local_time