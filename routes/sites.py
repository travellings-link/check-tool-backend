import flask, datetime
from routes.login import get_status_text
from helpers import startDB, closeDB, genData, genMsg

sites_bp = flask.Blueprint('sites', __name__)

# 获取一个还未被巡查的网站
@sites_bp.route('/site//', methods=['GET'])
def get_a_new_site():
   if get_status_text()['success'] == False:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] == 0:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   
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
      sql = "INSERT INTO logs (user, action, ip, timestamp) VALUES (%s, %s, %s, %s)"
      cursor.execute(sql, (get_status_text()['msg']['name'], f'巡查了一个网站，网站名称：{results[0][1]}', flask.request.headers.get('EO-Real-Client-IP'), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
      db.commit()
   except:
      return flask.jsonify(genMsg(False,'Unable to fetch or update data'))
   closeDB(db)
   if results != ():
      results = {"id": results[0][0],
                 "name": results[0][1],
                 "url": results[0][2],
                 "status": results[0][4],
                 "failedReason": results[0][5]
                 }
      return flask.jsonify(genData(True,results))
   else:
      return flask.jsonify(genMsg(True,'No unchecked sites'))

# 获取还未被巡查的网站列表
@sites_bp.route('/sites//', methods=['GET'])
def get_new_sites():
   if get_status_text()['success'] == False:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] == 0:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   try:
      sql = "SELECT * FROM webs WHERE isManualChecked IS NULL OR isManualChecked = False ORDER BY `webs`.`id` ASC"
      cursor.execute(sql)
      results = cursor.fetchall()
   except:
      return flask.jsonify(genMsg(False,'Unable to fetch data'))
   closeDB(db)
   if results != ():
      resultsList = []
      for i in results:
         resultsList.append({"id": i[0],
                 "name": i[1],
                 "url": i[2],
                 "status": i[4],
                 "failedReason": i[5]
                 })
      return flask.jsonify(genData(True,resultsList))
   else:
      return flask.jsonify(genMsg(True,'No unchecked sites'))

@sites_bp.route('/checkRestart//', methods=['GET'])
def restartCheck():
   if get_status_text()['success'] == False:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] != 1:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = 'UPDATE webs SET isManualChecked = False'
   cursor.execute(sql)
   sql = "INSERT INTO logs (user, action, ip, timestamp) VALUES (%s, %s, %s, %s)"
   cursor.execute(sql, (get_status_text()['msg']['name'], '重启了网站巡查', flask.request.headers.get('EO-Real-Client-IP'), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
   db.commit()
   closeDB(db)
   return flask.jsonify(genMsg(True,'Requested'))