import flask
from helpers import genData, genMsg, startDB, closeDB
from routes.login import get_status_text

count_bp = flask.Blueprint('count', __name__)

# 获取用户巡查的网站数量（根据cookies）
@count_bp.route('/count/', methods=['GET'])
def get_checked_count():
    if get_status_text()['success'] == False:
        return flask.jsonify(genMsg(False,'Permission Needed'))
    if get_status_text()['msg']['role'] == 0:
        return flask.jsonify(genMsg(False,'Permission Needed'))
    
    encryptedToken = flask.request.cookies.get('token')

    functions = startDB()
    db = functions[0]
    cursor = functions[1]
    
    sql = "SELECT count FROM checktoolusers WHERE encryptedToken = %s"
    try:
        cursor.execute(sql, (encryptedToken))
        results = cursor.fetchall()
        closeDB(db)
    except:
        closeDB(db)
        return flask.jsonify(genMsg(False,'Unable to fetch data'))
    
    return flask.jsonify(genData(True,{"count": results[0][0]}))

# 对该计数器进行递增
@count_bp.route('/count/increment/', methods=['POST'])
def increment_checked_count():
    if get_status_text()['success'] == False:
        return flask.jsonify(genMsg(False,'Permission Needed'))
    if get_status_text()['msg']['role'] == 0:
        return flask.jsonify(genMsg(False,'Permission Needed'))

    encryptedToken = flask.request.cookies.get('token')

    functions = startDB()
    db = functions[0]
    cursor = functions[1]

    sql = "UPDATE checktoolusers SET count = count + 1 WHERE encryptedToken = %s"
    try:
        cursor.execute(sql, (encryptedToken))
        db.commit()
    except:
        closeDB(db)
        return flask.jsonify(genMsg(False,'Unable to update data'))
    closeDB(db)

    return flask.jsonify(genMsg(True,"Count incremented successfully"))

# 对该计数器进行重置
@count_bp.route('/count/reset/', methods=['POST'])
def reset_checked_count():
    if get_status_text()['success'] == False:
        return flask.jsonify(genMsg(False,'Permission Needed'))
    if get_status_text()['msg']['role'] == 0:
        return flask.jsonify(genMsg(False,'Permission Needed'))

    encryptedToken = flask.request.cookies.get('token')

    functions = startDB()
    db = functions[0]
    cursor = functions[1]

    sql = "UPDATE checktoolusers SET count = 0 WHERE encryptedToken = %s"
    try:
        cursor.execute(sql, (encryptedToken))
        db.commit()
    except:
        closeDB(db)
        return flask.jsonify(genMsg(False,'Unable to update data'))
    closeDB(db)

    return flask.jsonify(genMsg(True,"Count reset successfully"))