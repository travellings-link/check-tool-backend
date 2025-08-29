import flask
import pymysql
import requests
import json
import Umodule
import hashlib
import datetime
import flask_cors

# 加载设置
import os
from dotenv import load_dotenv

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


app = flask.Flask('__name__')

flask_cors.CORS(app,
                origins=["http://localhost:5173", "https://check-tool.travellings.cn"],
                supports_credentials=True,
                allow_headers=["Content-Type", "Authorization", "Cookie"]
                )

# 跟 飞书 通信
clientID = os.getenv('OAUTH_clientID')
clientSecret = os.getenv('OAUTH_clientSecret')
redirect_uri = os.getenv('OAUTH_redirect_uri')

homepageUrl = os.getenv('homepageUrl')

@app.route('/login//', methods=['GET'])
def redirect2GitHub():
   requestUrl = f"https://accounts.feishu.cn/open-apis/authen/v1/authorize?client_id={clientID}&redirect_uri={redirect_uri}"
   return flask.redirect(requestUrl, code=301)

@app.route('/login/callback')
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
@app.route('/login/info//', methods=['GET'])
def get_status():
   token = flask.request.cookies.get('token')
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = f'SELECT * FROM checktoolusers WHERE encryptedToken = "{token}"'
   cursor.execute(sql)
   results = cursor.fetchall()

   if results == ():
      return flask.jsonify(Umodule.genMsg(False,'Have not logged in'))
   else:
      userData = {}
      userData['name'] = results[0][0]
      userData['role'] = results[0][2]
      userData['lastLogin'] = results[0][3]

      sql = f'UPDATE checktoolusers SET lastLogin = "{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}" WHERE encryptedToken = "{token}"'
      cursor.execute(sql)
      db.commit()
      closeDB(db)

      return flask.jsonify(Umodule.genMsg(True,userData))


def get_status_text():
   token = flask.request.cookies.get('token')
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = f'SELECT * FROM checktoolusers WHERE encryptedToken = "{token}"'
   cursor.execute(sql)
   results = cursor.fetchall()

   if results == ():
      return Umodule.genMsg(False,'Have not logged in')
   else:
      userData = {}
      userData['name'] = results[0][0]
      userData['role'] = results[0][2]
      userData['lastLogin'] = results[0][3]

   sql = f'UPDATE checktoolusers SET lastLogin = "{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}" WHERE encryptedToken = "{token}"'
   cursor.execute(sql)
   db.commit()
   closeDB(db)

   return Umodule.genMsg(True,userData)



# 获取一个还未被巡查的网站
@app.route('/site//', methods=['GET'])
def get_a_new_site():
   if get_status_text()['success'] == False:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] == 0:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]

   sql = "SELECT * FROM webs WHERE isManualChecked IS NULL OR isManualChecked = False ORDER BY `webs`.`id` ASC"
   try:
   # 执行SQL语句
      cursor.execute(sql)
   # 获取所有记录列表
      results = cursor.fetchall()
      sql = f'UPDATE webs SET isManualChecked = True WHERE id = {results[0][0]}'
      cursor.execute(sql)
      db.commit()
      closeDB(db)
   except:
      return flask.jsonify(Umodule.genMsg(False,'Unable to fetch or update data'))
   if results != ():
      results = {"id": results[0][0],
                 "name": results[0][1],
                 "url": results[0][2],
                 "status": results[0][4],
                 "failedReason": results[0][5]
                 }
      return flask.jsonify(Umodule.genData(True,results))
   else:
      return flask.jsonify(Umodule.genMsg(True,'No unchecked sites'))

# 获取还未被巡查的网站列表
@app.route('/sites//', methods=['GET'])
def get_new_sites():
   if get_status_text()['success'] == False:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] == 0:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   try:
      sql = "SELECT * FROM webs WHERE isManualChecked IS NULL OR isManualChecked = False ORDER BY `webs`.`id` ASC"
      cursor.execute(sql)
      results = cursor.fetchall()
      closeDB(db)
   except:
      return flask.jsonify(Umodule.genMsg(False,'Unable to fetch data'))
   if results != ():
      resultsList = []
      for i in results:
         resultsList.append({"id": i[0],
                 "name": i[1],
                 "url": i[2],
                 "status": i[4],
                 "failedReason": i[5]
                 })
      return flask.jsonify(Umodule.genData(True,resultsList))
   else:
      return flask.jsonify(Umodule.genMsg(True,'No unchecked sites'))

@app.route('/checkRestart//', methods=['GET'])
def restartCheck():
   if get_status_text()['success'] == False:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] != 1:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = 'UPDATE webs SET isManualChecked = False'
   cursor.execute(sql)
   db.commit()
   closeDB(db)
   return flask.jsonify(Umodule.genMsg(True,'Requested'))




# Abnormal Sites

# 这边并不直接删除网站，如需删除异常网站，需要前往成员列表删除。
# 这里是清除网站的WAIT属性，将状态改为RUN
@app.route('/AbnormalSites/<int:id>//', methods=['DELETE'])
def deleteAbnormalSites(id):
   if get_status_text()['success'] == False:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] != 1:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = "UPDATE webs SET status = 'RUN' WHERE id = %s"
   cursor.execute(sql, id)
   db.commit()
   return flask.jsonify(Umodule.genMsg(True,'Requested'))

# 仅更新状态（非机器误报）
# id放在uri，将内容异常之类的网站的状态改为WAIT
@app.route('/AbnormalSites/<int:id>//', methods=['PATCH'])
def submitAbormalSites(id):
   if get_status_text()['success'] == False:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] == 0:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = 'UPDATE webs SET status = "WAIT" WHERE id = %s'
   cursor.execute(sql, id)
   db.commit()
   return flask.jsonify(Umodule.genMsg(True,'Requested'))

#获取异常网站列表
@app.route('/AbnormalSites//', methods=['GET'])
def getAbnormalSites():
   if get_status_text()['success'] == False:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] != 1:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = "SELECT * FROM webs WHERE status = 'WAIT' ORDER BY `webs`.`id` ASC"
   try:
   # 执行SQL语句
      cursor.execute(sql)
   # 获取所有记录列表
      results = cursor.fetchall()
   except:
      return flask.jsonify(Umodule.genMsg(False,'Unable to fetch data'))
   closeDB(db)
   if results != ():
      resultsList = []
      for i in results:
         resultsList.append({"id": i[0],
                 "name": i[1],
                 "url": i[2],
                 "status": i[4]
                 })
      return flask.jsonify(Umodule.genData(True,resultsList))
   else:
      return flask.jsonify(Umodule.genMsg(True,'No abnormal sites'))





# CheckError

# 将被巡查机器误报的网站加到checkerror数据表

# 这边要加一点逻辑：防止误报网站重复提交！！！！！
@app.route('/CheckError/<int:id>//', methods=['POST'])
def submitCheckError(id):
   if get_status_text()['success'] == False:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] == 0:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = "SELECT * FROM webs WHERE `webs`.`id` = %s"
   try:
   # 执行SQL语句
      cursor.execute(sql, id)
   # 获取所有记录列表
      results = cursor.fetchall()
   except:
      return flask.jsonify(Umodule.genMsg(False,'Unable to fetch data'))
   if results != ():
      name = results[0][1]
      url = results[0][2]
      if results[0][5]:
         failedReason = results[0][5]
      else:
         failedReason = '无误报原因'
   else:
      return flask.jsonify(Umodule.genMsg(False,'unable to search the site data'))
   sql = f'SELECT * FROM checkerror WHERE name = "{name}"'
   cursor.execute(sql)
   results = cursor.fetchall()
   if results != ():
      return flask.jsonify(Umodule.genMsg(False,'Repeated sites'))
   sql = "INSERT INTO checkerror (name, url, errorReason) VALUES (%s, %s, %s)"
   toSubmitData = (name, url, failedReason)
   cursor.execute(sql, toSubmitData)
   db.commit()
   return flask.jsonify(Umodule.genMsg(True,'Requested'))

# 获取被巡查机器误报的网站
@app.route('/CheckError//', methods=['GET'])
def getCheckError():
   if get_status_text()['success'] == False:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] != 1:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = 'SELECT * FROM checkerror'
   try:
   # 执行SQL语句
      cursor.execute(sql)
   # 获取所有记录列表
      results = cursor.fetchall()
   except:
      return flask.jsonify(Umodule.genMsg(False,'Unable to fetch data'))
   closeDB(db)
   if results != ():
      resultsList = []
      for i in results:
         resultsList.append({"name": i[0],
                 "url": i[1],
                 "errorReason": i[2]
                 })
      return flask.jsonify(Umodule.genMsg(True,resultsList))
   else:
      return flask.jsonify(Umodule.genMsg(True,'No check error'))

@app.route('/CheckError/<name>//', methods=['DELETE'])
def deleteCheckError(name):
   if get_status_text()['success'] == False:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] != 1:
      return flask.jsonify(Umodule.genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   name = str(name)
   sql = "DELETE FROM checkerror WHERE name = %s"
   cursor.execute(sql, name)
   db.commit()
   return flask.jsonify(Umodule.genMsg(True,'Requested'))



app.run(debug=False)