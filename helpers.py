# 加载设置
import os
from dotenv import load_dotenv
import pymysql

load_dotenv(override=True)

def startDB():
   db = pymysql.connect(host=os.getenv('DB_HOST'),
                     user=os.getenv('DB_USER'),
                     password=os.getenv('DB_PASSWORD'),
                     database=os.getenv('DB_DATABASE'))
   cursor = db.cursor()
   return [db,cursor]

def closeDB(db):
   db.close()


def genMsg(ifSuccess, msg):
   result = {}
   result["success"] = bool(ifSuccess)
   result["msg"] = msg
   return result

def genData(ifSuccess, data):
   result = {}
   result["success"] = bool(ifSuccess)
   result["data"] = data
   return result

def SecureUserInputText(text):
   text = text.replace("<", "&lt;")
   text = text.replace(">", "&gt;")
   text = text.replace("'", "&#39;")
   text = text.replace('"', "&quot;")
   text = text.replace("\n", "<br>")
   text = text.replace("\r", "")
   text = text.replace(";", "")
   return text