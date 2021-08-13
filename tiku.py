#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 @FileName: 强国题库.py
 @Date: 2020/12/2 10:30
 @Description:
"""
import json
import time

# import requests
from bottle import route, run, static_file, request
import sqlite3


class DbTool:
	def __init__(self):
		self.db = sqlite3.connect('tiku.db')
		self.c = self.db.cursor()

	def close(self):
		"""
		关闭数据库
		"""
		self.c.close()
		self.db.close()

	def execute(self, sql, param=None):
		"""
		执行数据库的增、删、改
		sql：sql语句
		param：数据，可以是list或tuple，亦可是None
		retutn：成功返回True
		"""
		# print('sql=', sql, 'param=', param)
		try:
			if param is None:
				self.c.execute(sql)
			else:
				if type(param) is list:
					self.c.executemany(sql, param)
				else:
					self.c.execute(sql, param)
			count = self.db.total_changes
			self.db.commit()
		except Exception as e:
			print('Exception:', e)
			return False
		if count > 0:
			return True
		else:
			print('删除了0行')
			return False

	def query(self, sql, param=None):
		"""
		查询语句
		sql：sql语句
		param：参数,可为None
		retutn：成功返回True
		"""
		# print('sql=', sql, 'param=', param)
		if param is None:
			self.c.execute(sql)
		else:
			self.c.execute(sql, param)
		return self.c.fetchall()


@route("/<path:path>")
def callback(path):
	return static_file(path, "")  # 指定静态文件目录assets


@route('/datalist')
def index():
	return static_file('index.html', root='.')


@route('/insertOrUpdate', method=['POST'])
def insertOrUpdate():
	f = request.POST.decode('utf-8')
	question = f.get('question')
	answer = f.get('answer')
	tableName = request.GET.decode('utf-8').get('table_name', 'tiku')
	print('question=', question, 'answer=', answer)
	t = time.strftime('%Y-%m-%d %H:%M:%S')
	db = DbTool()
	q = db.query('select * from ' + tableName + ' where question = "' + question + '" and answer = "' + answer + '"')
	if not len(q):
		result = db.execute('insert into ' + tableName + '(question,answer,datetime) values (?,?,?)',
							(question, answer, t))
		return json.dumps(200 if result else 500)
	else:
		return json.dumps(202)


@route('/search', method=['GET'])
def search():
	keyword = request.GET.decode('utf-8').get('keyword', '')
	tableName = request.GET.decode('utf-8').get('table_name', 'tiku')
	page = int(request.GET.decode('utf-8').get('page', 1))
	rows = int(request.GET.decode('utf-8').get('rows', 10))
	limit = (page - 1) * rows
	db = DbTool()
	total = db.query(
		'select count(*) from ' + tableName + ' where question like ' + '"%' + keyword + '%"' + 'or answer like ' + '"%' + keyword + '%"')
	result = db.query(
		'select question,answer,datetime from ' + tableName + ' where question like ' + '"%' + keyword + '%"' + 'or answer like ' + '"%' + keyword + '%" LIMIT ' +
		str(limit) + ',' + str(rows))
	data = {'total': total[0][0], 'rows': []}
	for r in result:
		# data['rows'].append({'id': r[0], 'question': r[1], 'answer': r[2], 'datetime': 0})
		data['rows'].append({'id': 0, 'question': r[0], 'answer': r[1], 'datetime': r[2]})
	###################################将tikuNet表中的题库，插入到tiku表中###############
	# question = r[1]
	# answer = r[2]
	# db = DbTool()
	# q = db.query('select * from ' + 'tiku' + ' where question = "' + question + '" and answer = "' + answer + '"')
	# if not len(q):
	# 	result = db.execute('insert into ' + 'tiku' + '(question,answer) values (?,?)', (question, answer))
	# 	print(result)
	###################################将tikuNet表中的题库，插入到tiku表中###############
	return json.dumps(data)


@route('/searchRepeatData', method=['GET'])
def searchRepeatData():
	tableName = request.GET.decode('utf-8').get('table_name', 'tiku')
	db = DbTool()
	q = 'SELECT question,answer,datetime FROM ' + tableName + '  WHERE ( question ) IN (SELECT question FROM ' + tableName + '  GROUP BY question HAVING count( question ) > 1)'
	result = db.query(q)
	data = {'total': len(result), 'rows': []}
	for r in result:
		# data['rows'].append({'id': r[0], 'question': r[1], 'answer': r[2], 'datetime': 0})
		data['rows'].append({'id': 0, 'question': r[0], 'answer': r[1], 'datetime': r[2]})
	return json.dumps(data)


@route('/deleteById', method=['GET'])
def deleteById():
	q = request.query.decode('utf-8').get('q')
	a = request.query.decode('utf-8').get('a')
	tableName = request.GET.decode('utf-8').get('table_name', 'tiku')
	ids = request.GET.decode('utf-8').get('ids[]')
	if ids:
		for item in json.loads(ids):
			deleteQ(tableName, item['q'], item['a'])
	else:
		deleteQ(tableName, q, a)
	return json.dumps(200)


def deleteQ(t, q, a):
	db = DbTool()
	# res = db.execute('delete from ' + tableName + ' where id in ' + ids)
	sql = 'delete from ' + t + ' where question = "' + q + '" and answer = "' + a + '"'
	res = db.execute(sql)
	return res


@route('/onekeyclear', method=['GET'])
def onekeyclear():
	tableName = request.GET.decode('utf-8').get('table_name', 'tiku')
	sql = """
		DELETE 
		FROM
			""" + tableName + """
		WHERE
			( """ + tableName + """.question,""" + tableName + """.answer ) IN ( SELECT question,answer FROM """ + tableName + """ GROUP BY question,answer HAVING count( * ) > 1 ) 
			AND rowid NOT IN (
		SELECT
			min( rowid ) 
		FROM
			""" + tableName + """ 
		GROUP BY
			question,answer 
		HAVING
			count( * ) > 1)
	"""
	db = DbTool()
	res = db.execute(sql)
	return json.dumps(200 if res else 500)


@route('/getAnswerByQuestion')
def getAnswerByQuestion():
	# tableName = request.GET.decode('utf-8').get('table_name', 'tiku')
	# question = request.GET.decode('utf-8').get('question', '')
	# if question.startswith("'") and question.startswith("'"):
	# 	question = question[1: -1]
	# if question.startswith('"') and question.startswith('"'):
	# 	question = question[1: -1]
	# print('question:', question)
	# db = DbTool()
	# # select question,answer,datetime from tiku where question like "%aa%"or answer like "%aa%" LIMIT 0,10
	# sql = 'select answer from ' + tableName + ' where question like "%' + question + '%"'
	# print(sql)
	# result = db.query(sql)
	# return result[0][0]
	
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
	return JsonStr


# q = db.query('select * from ' + tableName + ' where question = "' + question + '" and answer = "' + answer + '"')
# if not len(q):
# 	result = db.execute('insert into ' + tableName + '(question,answer,datetime) values (?,?,?)',
# 						(question, answer, t))
# 	return json.dumps(200 if result else 500)
# else:
# 	return json.dumps(202)

run(host='0.0.0.0', port=1234)
# run(host='localhost', port=8088)
