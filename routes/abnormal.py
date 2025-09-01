import flask
from helpers import genData, genMsg, startDB, closeDB
from routes.login import get_status_text
import datetime

abnormal_bp = flask.Blueprint('abnormal', __name__)

# Abnormal Sites

# 这边并不直接删除网站，如需删除异常网站，需要前往成员列表删除。
# 这里是清除网站的WAIT属性，将状态改为RUN
@abnormal_bp.route('/AbnormalSites/<int:id>//', methods=['DELETE'])
def deleteAbnormalSites(id):
   if get_status_text()['success'] == False:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] != 1:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = "UPDATE webs SET status = 'RUN' WHERE id = %s;"
   cursor.execute(sql, id)
   sql = "INSERT INTO logs (user, action, ip, timestamp) VALUES (%s, %s, %s, %s)"
   cursor.execute(sql, (get_status_text()['msg']['name'], f'撤销非误报异常站点的误报标记，网站ID：{id}', flask.request.headers.get('EO-Real-Client-IP'), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
   db.commit()
   return flask.jsonify(genMsg(True,'Requested'))

# 仅更新状态（非机器误报）
# id放在uri，将内容异常之类的网站的状态改为WAIT
@abnormal_bp.route('/AbnormalSites/<int:id>//', methods=['PATCH'])
def submitAbormalSites(id):
   if get_status_text()['success'] == False:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] == 0:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   
   functions = startDB()
   db = functions[0]
   cursor = functions[1]
   sql = 'UPDATE webs SET status = "WAIT" WHERE id = %s'
   cursor.execute(sql, id)
   sql = "INSERT INTO logs (user, action, ip, timestamp) VALUES (%s, %s, %s, %s)"
   cursor.execute(sql, (get_status_text()['msg']['name'], f'提交非误报异常站点，网站ID：{id}', flask.request.headers.get('EO-Real-Client-IP'), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
   db.commit()
   return flask.jsonify(genMsg(True,'Requested'))

#获取异常网站列表
@abnormal_bp.route('/AbnormalSites//', methods=['GET'])
def getAbnormalSites():
   if get_status_text()['success'] == False:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   if get_status_text()['msg']['role'] != 1:
      return flask.jsonify(genMsg(False,'Permission Needed'))
   
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
      return flask.jsonify(genMsg(False,'Unable to fetch data'))
   closeDB(db)
   if results != ():
      resultsList = []
      for i in results:
         resultsList.append({"id": i[0],
                 "name": i[1],
                 "url": i[2],
                 "status": i[4]
                 })
      return flask.jsonify(genData(True,resultsList))
   else:
      return flask.jsonify(genMsg(True,'No abnormal sites'))