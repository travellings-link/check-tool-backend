import flask
from helpers import genMsg, startDB, closeDB
from routes.login import get_status_text
import datetime

checkerror_bp = flask.Blueprint('checkerror', __name__)

# CheckError

# 将被巡查机器误报的网站加到checkerror数据表

# 这边要加一点逻辑：防止误报网站重复提交！！！！！
@checkerror_bp.route('/CheckError/<int:id>//', methods=['POST'])
def submitCheckError(id):
   if get_status_text()['success'] == False:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] == 0:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   
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
      return flask.jsonify(genMsg(False,'Unable to fetch data'))
   if results != ():
      name = results[0][1]
      url = results[0][2]
      if results[0][5]:
         failedReason = results[0][5]
      else:
         failedReason = '无误报原因'
   else:
      return flask.jsonify(genMsg(False,'unable to search the site data'))
   sql = f'SELECT * FROM checkerror WHERE name = "{name}"'
   cursor.execute(sql)
   results = cursor.fetchall()
   if results != ():
      return flask.jsonify(genMsg(False,'Repeated sites'))
   sql = "INSERT INTO checkerror (name, url, errorReason) VALUES (%s, %s, %s)"
   toSubmitData = (name, url, failedReason)
   cursor.execute(sql, toSubmitData)
   sql = "INSERT INTO logs (user, action, ip, timestamp) VALUES (%s, %s, %s, %s)"
   cursor.execute(sql, (get_status_text()['msg']['name'], f'提交巡查机器误报站点，网站ID：{id}', flask.request.headers.get('EO-Real-Client-IP'), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
   db.commit()
   return flask.jsonify(genMsg(True,'Requested'))

# 获取被巡查机器误报的网站
@checkerror_bp.route('/CheckError//', methods=['GET'])
def getCheckError():
   if get_status_text()['success'] == False:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] != 1:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   
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
      return flask.jsonify(genMsg(False,'Unable to fetch data'))
   closeDB(db)
   if results != ():
      resultsList = []
      for i in results:
         resultsList.append({"name": i[0],
                 "url": i[1],
                 "errorReason": i[2]
                 })
      return flask.jsonify(genMsg(True,resultsList))
   else:
      return flask.jsonify(genMsg(True,'No check error'))

@checkerror_bp.route('/CheckError/<name>//', methods=['DELETE'])
def deleteCheckError(name):
   if get_status_text()['success'] == False:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] != 1:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   name = str(name)
   sql = "DELETE FROM checkerror WHERE name = %s"
   cursor.execute(sql, name)
   sql = "INSERT INTO logs (user, action, ip, timestamp) VALUES (%s, %s, %s, %s)"
   cursor.execute(sql, (get_status_text()['msg']['name'], f'删除巡查机器误报站点，网站名称：{name}', flask.request.headers.get('EO-Real-Client-IP'), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
   db.commit()
   return flask.jsonify(genMsg(True,'Requested'))