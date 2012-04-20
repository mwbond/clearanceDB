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
	def editList(self, string, index, value):
		split = string.split(';')
		split[index] = value
		return ';'.join(split)
	def calcYAR(self, length, speed, grade, turn):
		if (length==0) or (speed==0):
			return '-', '-'
		if turn:
			min_r = 0.5
			speed = 20
		else:
			min_r = 1
			speed = speed + 5

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
		if yellow=='-':
			yellow = 0
		pct = length / 3.5
		fdw = pct - (float(yellow) + float(red) - 3)
		fdw = max(4.0, fdw)
		fdw = ceil(fdw)
		return str(fdw)
	def POST(self):
		form = dict(web.input())
		lag = []
		if 'major' not in form:
			for index in range(8):
				yar_length = form['yar_len'].split(';')[index]
				yar_length = int(float(yar_length or 0))

				fdw_length = form['fdw_len'].split(';')[index]
				fdw_length = int(float(fdw_length or 0))

				speed = form['speed'].split(';')[index]
				speed = float(speed or 0)

				grade = form['grade'].split(';')[index]
				grade = float(grade or 0)

				mov = form['mov'].split(';')[index]

				yellow, red = self.calcYAR(yar_length, speed, grade, mov)
				print yellow
				print red
				fdw = self.calcFDW(fdw_length, red, yellow)
				
				form ['yellow'] = self.editList(form['yellow'], index, yellow)
				form ['red'] = self.editList(form['red'], index, red)
				form ['fdw'] = self.editList(form['fdw'], index, fdw)

				adj = form['lag'].split(';')[index]
				if adj:
					lag.append([index, int(adj)])

			for index, adj in lag:
				yellow = max(form['yellow'].split(';')[index], form['yellow'].split(';')[adj])
				red = max(form['red'].split(';')[index], form['red'].split(';')[adj])
				fdw = max(form['fdw'].split(';')[index], form['fdw'].split(';')[adj])
				form ['yellow'] = self.editList(form['yellow'], index, yellow)
				form ['yellow'] = self.editList(form['yellow'], adj, yellow)
				form ['red'] = self.editList(form['red'], index, red)
				form ['red'] = self.editList(form['red'], adj, red)
				form ['fdw'] = self.editList(form['fdw'], index, fdw)
				form ['fdw'] = self.editList(form['fdw'], adj, fdw)

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
