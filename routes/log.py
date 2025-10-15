import flask
from helpers import startDB, closeDB, genMsg, genData, SecureUserInputText
from routes.login import get_status_text

log_bp = flask.Blueprint('log', __name__)

@log_bp.route('/log//', methods=['GET'])
def getlog():
    if get_status_text()['success'] == False:
      return flask.jsonify(genMsg(False,'Permission Needed'))
    if get_status_text()['msg']['role'] == 0:
      return flask.jsonify(genMsg(False,'Permission Needed'))

    functions = startDB()
    db = functions[0]
    cursor = functions[1]

    sql = "SELECT * FROM logs ORDER BY `logs`.`id` DESC"
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        closeDB(db)
    except:
        closeDB(db)
        return flask.jsonify(genMsg(False,'Unable to fetch data'))
    if results != ():
        resultsList = []
        for i in results:
            resultsList.append({"id": i[0],
                                "user": i[1],
                                "action": i[2],
                                "ip": i[3],
                                "timestamp": i[4]
                                })
        return flask.jsonify(genData(True,resultsList))
    else:
        return flask.jsonify(genMsg(True,'No logs found'))

@log_bp.route('/log/<id>/', methods=['DELETE'])
def delete_log(id):
    if get_status_text()['success'] == False:
        return flask.jsonify(genMsg(False,'Permission Needed'))
    if get_status_text()['msg']['role'] != 1:
        return flask.jsonify(genMsg(False,'Permission Needed'))

    id = SecureUserInputText(id)
    
    functions = startDB()
    db = functions[0]
    cursor = functions[1]

    if id == 'all':
        sql = "DELETE FROM logs"
        cursor.execute(sql)
    else:
        sql = "DELETE FROM logs WHERE id = %s"
        cursor.execute(sql, (id,))
    db.commit()
    closeDB(db)
    return flask.jsonify(genMsg(True,'Log deleted'))

@log_bp.route('/log/user/', methods=['GET'])
def get_log():
    if get_status_text()['success'] == False:
        return flask.jsonify(genMsg(False,'Permission Needed'))
    if get_status_text()['msg']['role'] == 0:
        return flask.jsonify(genMsg(False,'Permission Needed'))

    functions = startDB()
    db = functions[0]
    cursor = functions[1]

    user = flask.request.args.get('user')

    sql = "SELECT * FROM logs WHERE user = %s"
    cursor.execute(sql, (user,))
    result = cursor.fetchone()
    closeDB(db)
    if result:
        log_data = {
            "id": result[0],
            "action": result[2],
            "ip": result[3],
            "timestamp": result[4]
        }
        return flask.jsonify(genData(True, log_data))
    else:
        return flask.jsonify(genMsg(False,'Log not found'))