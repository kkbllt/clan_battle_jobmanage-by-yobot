# -*- coding: utf-8 -*- #
'''
工会作业管理插件
'''
import os
import peewee as pw

db = pw.SqliteDatabase(
	os.path.join('./yobot_data/','zy.db')
)


class dor(pw.Model):
	group_id = pw.IntegerField(default=0)
	pr_user_id = pw.IntegerField(default=0)
	bossid = pw.CharField()
	team = pw.CharField()
	team_int = pw.CharField()
	dmg = pw.CharField()
	msg = pw.CharField(null = True)
	jobid = pw.CharField()
	jobdelcode = pw.CharField(default=0)
	jobDelTimeLine = pw.IntegerField(default=0)

	class Meta:
		database = db
		primary_key = pw.CompositeKey('group_id','pr_user_id','bossid','team','team_int','dmg','jobid','jobDelTimeLine')

class logs(pw.Model):
	group_id = pw.IntegerField(default=0)
	user_id = pw.IntegerField(default=0)
	jobdelcode = pw.IntegerField(default=0)
	jobDelTime = pw.IntegerField(default=0)

	class Meta:
		database = db

def data():
	if not os.path.exists(os.path.join('./yobot_data/','zy.db')):
		db.connect()
		db.create_tables([dor])
		db.create_tables([logs])
		db.close()

data()