import flask
import requests
import json
import hashlib
import datetime
import os
from dotenv import load_dotenv
from helpers import startDB, closeDB, genData, genMsg


login_bp = flask.Blueprint('login', __name__)

load_dotenv(override=True)

# 跟 飞书 通信
clientID = os.getenv('OAUTH_clientID')
clientSecret = os.getenv('OAUTH_clientSecret')
redirect_uri = os.getenv('OAUTH_redirect_uri')

homepageUrl = os.getenv('homepageUrl')


@login_bp.route('/login//', methods=['GET'])
def redirect2GitHub():
   requestUrl = f"https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id={clientID}&redirect_uri={redirect_uri}"
   return flask.redirect(requestUrl, code=301)

@login_bp.route('/login/callback')
def Feishucallback():
    code = flask.request.args.get('code')
    requestUrl = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        "Content-Type": "application/json; charset=utf-8"
    }
    body = {
        "grant_type": "authorization_code",
        "client_id": clientID,
        "client_secret": clientSecret,
        "code": code,
        "redirect_uri": redirect_uri
    }
    body = json.dumps(body)
    
    try:
        # 获取access_token
        x = requests.post(requestUrl, headers=headers, data=body)
        response_data = x.json()
        
        # 检查飞书返回的code字段
        if response_data.get('code') != 0:
            error_msg = response_data.get('error_description', '未知错误')
            print(f"飞书OAuth错误: {error_msg}")
            return f"OAuth认证失败: {error_msg}", 400
        
        # 正确的获取access_token方式
        access_token = response_data["access_token"]
        encryptedToken = hashlib.md5(access_token.encode('utf-8')).hexdigest()

        # 获取用户信息
        dataUrl = "https://open.feishu.cn/open-apis/authen/v1/user_info"
        dataHeaders = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
            "Accept": "application/json",
            'Authorization': f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        y = requests.get(dataUrl, headers=dataHeaders)
        user_data = y.json()
        
        # 检查用户信息请求是否成功
        if user_data.get('code') != 0:
            print(f"获取用户信息失败: {user_data}")
            return "获取用户信息失败", 400
        
        # 获取用户名 - 根据飞书文档，用户姓名字段是"name"
        username = user_data["data"]["name"]

        # 数据库操作
        functions = startDB()
        db = functions[0]
        cursor = functions[1]
        
        sql = f'SELECT * FROM checktoolusers WHERE name = "{username}"'
        cursor.execute(sql)
        results = cursor.fetchall()

        if not results:
            sql = f'INSERT INTO checktoolusers (name, encryptedToken, role, lastLogin) VALUES ("{username}", "{encryptedToken}", 0, "{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")'
            cursor.execute(sql)
            db.commit()
        else:
            sql = f'UPDATE checktoolusers SET encryptedToken = "{encryptedToken}", lastLogin = "{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}" WHERE name = "{username}"'
            cursor.execute(sql)
            db.commit()
        
        closeDB(db)

        # 重定向到首页并设置cookie
        rsp = flask.redirect(homepageUrl)
        rsp.set_cookie(
            key='token',
            value=encryptedToken,
            httponly=True,
        )
        return rsp
        
    except KeyError as e:
        print(f"KeyError: {e}")
        print(f"飞书响应: {response_data}")
        print(f"用户信息响应: {user_data if 'user_data' in locals() else '未获取'}")
        return "OAuth认证失败，请检查配置", 400
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return "服务器内部错误", 500


# 用户系统
@login_bp.route('/login/info//', methods=['GET'])
def get_status():
   token = flask.request.cookies.get('token')
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = f'SELECT * FROM checktoolusers WHERE encryptedToken = "{token}"'
   cursor.execute(sql)
   results = cursor.fetchall()

   if results == ():
      return flask.jsonify(genMsg(False,'Have not logged in'))
   else:
      userData = {}
      userData['name'] = results[0][0]
      userData['role'] = results[0][2]
      userData['lastLogin'] = results[0][3]

      sql = f'UPDATE checktoolusers SET lastLogin = "{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}" WHERE encryptedToken = "{token}"'
      cursor.execute(sql)
      db.commit()
      closeDB(db)

      return flask.jsonify(genMsg(True,userData))


def get_status_text():
   token = flask.request.cookies.get('token')
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = f'SELECT * FROM checktoolusers WHERE encryptedToken = "{token}"'
   cursor.execute(sql)
   results = cursor.fetchall()

   if results == ():
      return genMsg(False,'Have not logged in')
   else:
      userData = {}
      userData['name'] = results[0][0]
      userData['role'] = results[0][2]
      userData['lastLogin'] = results[0][3]

   sql = f'UPDATE checktoolusers SET lastLogin = "{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}" WHERE encryptedToken = "{token}"'
   cursor.execute(sql)
   db.commit()
   closeDB(db)

   return genMsg(True,userData)