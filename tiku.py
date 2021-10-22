from flask import Flask, request, render_template, g
from flask import json
from flask.json import jsonify
from werkzeug.utils import escape
import sqlite3, time


DATABASE = './tiku.db'
app = Flask(__name__)
app.secret_key = 'please-generate-a-random-secret_key$'
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.before_request
def before_request():
    g.db = sqlite3.connect(DATABASE)


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def execute(sql, param=None):
    """
    执行数据库的增、删、改
    sql：sql语句
    param：数据，可以是list或tuple，亦可是None
    return：成功返回True
    """
    try:
        if param is None:
            g.db.execute(sql)
        else:
            if isinstance(param, list):
                g.db.executemany(sql, param)
            else:
                g.db.execute(sql, param)
        count = g.db.total_changes
        g.db.commit()
    except Exception as e:
        print('Exception:', e)
        return False
    return True if count > 0 else False


def query(sql, param=None):
    """
    查询语句
    sql：sql语句
    param：参数,可为None
    """
    cur = g.db.execute(sql, param) if param else g.db.execute(sql)
    return cur.fetchall()


def deleteQ(t, q, a):
	# res = db.execute('delete from ' + tableName + ' where id in ' + ids)
	sql = f'delete from {t} where question = "{q}" and answer = "{a}"'
	execute(sql)


def editQ(table, q, a, new_a):
	sql = f'UPDATE {table} SET answer = "{new_a}" WHERE question = "{q}" and answer = "{a}"'
	execute(sql)


@app.route('/')
def index():
	return render_template('index.html')
	
@app.route('/tableCount')
def tableCount():
	#创建一个链接
	conn = sqlite3.connect("tiku.db")
	#创建一个游标 curson
	cursor = conn.cursor()
	#查询一条记录：
	sql = "SELECT COUNT(answer)  FROM `tiku`"
	print(sql)
	cursor.execute(sql)
	#获取查询结果：
	values = cursor.fetchall()
	return json.dumps( values, ensure_ascii=False )


@app.route('/insertOrUpdate', methods=['POST'])
def insert_or_update():
    if request.method == "POST":
        question, answer = request.form['question'], request.form['answer']
        tableName = request.form.get('table_name', 'tiku')
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        q = query(f'select * from {tableName} where question = "{question}" and answer = "{answer}"')
        if not len(q):
            result = execute(f'insert into {tableName}(question,answer,datetime) values (?,?,?)', (question, answer, t))
            return jsonify(200 if result else 500)
        else:
            return jsonify(202)



@app.route('/search', methods=['GET'])
def search():
	keyword = request.args.get('keyword') if request.args.get('keyword') else ''
	tableName = request.args.get('table_name', 'tiku')
	page = int(request.args.get('page', 1))
	rows = int(request.args.get('rows', 10))
	limit = (page - 1) * rows
	total = query(f'select count(*) from {tableName} where question like "%{keyword}%"or answer like "%{keyword}%"')
	result = query(f'select question,answer,datetime from {tableName} where question like "%{keyword}%"or answer like "%{keyword}%" LIMIT {limit},{rows}')
	data = {'total': total[0][0]}
	# for r in result:
	# 	# data['rows'].append({'id': r[0], 'question': r[1], 'answer': r[2], 'datetime': 0})
	# 	data['rows'].append({'question': r[0], 'answer': r[1], 'datetime': r[2]})
	data['rows'] = [{'question': r[0], 'answer': r[1], 'datetime': r[2]} for r in result]
	###################################将tikuNet表中的题库，插入到tiku表中###############
	# question = r[1]
	# answer = r[2]
	# db = DbTool()
	# q = db.query('select * from ' + 'tiku' + ' where question = "' + question + '" and answer = "' + answer + '"')
	# if not len(q):
	# 	result = db.execute('insert into ' + 'tiku' + '(question,answer) values (?,?)', (question, answer))
	# 	print(result)
	###################################将tikuNet表中的题库，插入到tiku表中###############
	return jsonify(data)


@app.route('/searchRepeatData', methods=['GET'])
def searchRepeatData():
	tableName = request.args.get('table_name', 'tiku')
	q = f'SELECT question,answer,datetime FROM {tableName} WHERE ( question ) IN (SELECT question FROM {tableName} GROUP BY question HAVING count( question ) > 1)'
	result = query(q)
	data = {'total': len(result), 'rows': []}
	for r in result:
		# data['rows'].append({'id': r[0], 'question': r[1], 'answer': r[2], 'datetime': 0})
		data['rows'].append({'id': 0, 'question': r[0], 'answer': r[1], 'datetime': r[2]})
	return jsonify(data)


@app.route('/deleteById', methods=['GET'])
def deleteById():
	ids = request.args.get('ids[]')
	if ids:
		for item in json.loads(ids):
			deleteQ('tiku', item['q'], item['a'])
	else:
		q = request.args.get('q')
		a = request.args.get('a')
		tableName = request.args.get('table_name', 'tiku')
		deleteQ(tableName, q, a)
	return jsonify(200)


@app.route('/editById', methods=['GET'])
def editById():
	q, a, new_a = request.args.get('q'), request.args.get('a'), request.args.get('new_a')
	editQ('tiku', q, a, new_a)
	return jsonify(200)


@app.route('/onekeyclear', methods=['GET'])
def onekeyclear():
	tableName = 'tiku'
	sql = f"delete from {tableName} where {tableName}.rowid not in (select MAX({tableName}.rowid) from {tableName} group by question)"
	res = execute(sql)
	return jsonify(200 if res else 500)


@app.route('/getAnswerByQuestion')
def getAnswerByQuestion():
	#创建一个链接
	conn = sqlite3.connect("tiku.db")
	#创建一个游标 curson
	cursor = conn.cursor()
	#查询一条记录：
	sql = "SELECT * FROM `tiku`"
	print(sql)
	cursor.execute(sql)
	#获取查询结果：
	values = cursor.fetchall()
	JsonStr = json.dumps( values, ensure_ascii=False ) 
	conn.close()
	return JsonStr

if __name__ == '__main__':
	host_ = '0.0.0.0'
	port_ = '8008'
	app.run(host=host_, port=port_)