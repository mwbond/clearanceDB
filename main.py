import csv
import cStringIO
import web
from math import ceil

import db

urls = ('/', 'home',
		'/update_location', 'update_location',
		'/overview', 'overview',
		'/intersection', 'intersection',
		'/add_entry', 'add_entry',
		'/batch_process', 'batch_process',
		'/update_intersection', 'update_intersection',
		'/output', 'output',
		'/(.*)/', 'redirect')

class home:
	def GET(self):
		render = web.template.render('templates')
		location = db.get_info()['location']
		if location:
			return render.home(location)
		return render.home('Unknown')
	def POST(self):
		db_info = []
		form = web.input()
		layout_txt = form.layoutfile
		f = cStringIO.StringIO(layout_txt)
		for line in f:
			db_info.append(line.rstrip().split(','))
		for int_id, int_name in db_info:
			int_major, int_minor = int_name.split('&')
			db.modify(int_id=int_id, major=int_major.rstrip(), minor=int_minor.lstrip())
		raise web.seeother('/')

class update_location:
	def POST(self):
		form = dict(web.input())
		db.modify(**form)
		raise web.seeother('/')

class overview:
	def GET(self):
		db_info = db.get_db_info()
		render = web.template.render('templates')
		return render.overview(db_info)

class intersection:
	def GET(self):
		int_id = web.input().IntID
		kwargs = db.get_info(int_id)
		#DEFAULTS
		if not kwargs['map_lat']:
			kwargs['map_lat'] = '39.26'
			kwargs['map_lng'] = '-76.67'
		if not kwargs['map_zoom']:
			kwargs['map_zoom'] = '18'
		render = web.template.render('templates')
		return render.intersection(kwargs)

class update_intersection:
	def calcYAR(self, length, speed, grade, turn):
		if turn:
			min_r = 0.5
			speed = 20
		else:
			min_r = 1
			speed = speed + 5
		if (length==0) or (speed==0):
			return '-', '-'

		yellow = 1 + (0.733 * speed)/(10 + (0.32 * grade))
		yellow_r = ceil(2 * yellow)/2
		yellow = round(yellow, 1)
		red = length / speed
		red_r = ceil(2 * red)/2
		red = round(red, 1)
		diff_yellow = yellow - yellow_r
		diff_red = red - red_r

		yellow_r = min(yellow_r, 6)
		yellow_r = max(yellow_r, 4)
		red_r = min(red_r, 3)
		red_r = max(red_r, min_r)
		if(diff_yellow + diff_red) < 0:
			yellow_r = yellow_r + 0.5
		return str(yellow_r / 1.0), str(red_r / 1.0)
	def calcFDW(self, length, red, yellow):
		if length==0:
			return '-'
		if red=='-':
			red = 0
		pct = length / 3.5
		fdw = pct - (float(yellow) + float(red) - 3)
		fdw = max(4.0, fdw)
		fdw = ceil(fdw)
		return str(fdw)
	def POST(self):
		phases = ['1', '2', '3', '4', '5', '6', '7', '8']
		form = dict(web.input())
		lag = []
		if 'major' not in form:
			for p in phases:
				p = 'p' + p + '_'
				yar_length = form[p + 'yar_len']
				if yar_length:
					yar_length = int(float(yar_length))
				else:
					yar_length = 0
				fdw_length = form[p + 'fdw_len']
				if fdw_length:
					fdw_length = int(float(form[p + 'fdw_len']))
				else:
					fdw_length = 0
				speed = form[p + 'speed']
				if speed:
					speed = float(speed)
				else:
					speed = 0
				grade = form[p + 'grade']
				mov = form[p + 'mov']
				if grade:
					grade = int(float(grade))
				else:
					grade = 0
				yellow, red = self.calcYAR(yar_length, speed, grade, mov)
				fdw = self.calcFDW(fdw_length, red, yellow)
				form[p + 'y'] = yellow
				form[p + 'r'] = red
				form[p + 'f'] = fdw
				if (p + 'lag') in form:
					if form[p + 'lag'] in phases:
						adj = 'p' + form[p + 'lag'] + '_'
						lag.append([p, adj])
			for phase in lag:
				yellow = max(form[phase[0] + 'y'], form[phase[1] + 'y'])
				red = max(form[phase[0] + 'r'], form[phase[1] + 'r'])
				fdw = max(form[phase[0] + 'f'], form[phase[1] + 'f'])
				form[phase[0] + 'y'] = yellow
				form[phase[1] + 'y'] = yellow
				form[phase[0] + 'r'] = red
				form[phase[1] + 'r'] = red
				form[phase[0] + 'f'] = fdw
				form[phase[1] + 'f'] = fdw

		db.modify(**form)
		raise web.seeother('/intersection' + '?IntID=' + form['int_id'])

class add_entry:
	def POST(self):
		form = dict(web.input())
		db.modify(**form)
		raise web.seeother('/overview')

class output:
	def GET(self):
		int_id = web.input().IntID
		kwargs = db.get_info(int_id)
		render = web.template.render('templates')
		return render.output(kwargs)

class batch_process:
	def POST(self):
		form = web.input(IntID=[])
		if form['process'] == 'Delete Intersections':
			for int_id in form['IntID']:
				db.delete_id(int_id)
		elif form['process'] == 'Create PDFs':
			print 'PDF'
			for int_id in form['IntID']:
				print int_id
		raise web.seeother('/overview')

class redirect:
	def GET(self, path):
		web.seeother('/' + path)

app = web.application(urls, locals())
if __name__ == '__main__':
	app.run()
