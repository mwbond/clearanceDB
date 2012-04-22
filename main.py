import csv
import cStringIO
import web
from math import ceil

import db

num_phases = 8

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

		render = web.template.render('templates', globals={'map': map, 'str': str, 'zip': zip})
		return render.intersection(kwargs)

class update_intersection:
	def POST(self):
		form = dict(web.input())
		db.modify(**form)
		raise web.seeother('/intersection' + '?IntID=' + form['int_id'])

class add_entry:
	def POST(self):
		form = dict(web.input())
		db.modify(**form)
		raise web.seeother('/overview')

class output:
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
	def calcPed(self, length, red, yellow):
		min_walk = 7
		if length==0:
			return '-', '-', '-'
		if red=='-':
			red = 0
		if yellow=='-':
			yellow = 0
		pct = length / 3.5
		walk = round(max((length + 6)/3 - pct, min_walk))
		fdw = pct - (float(yellow) + float(red))
		pct = round(pct)
		fdw = round(max(4.0, fdw))
		return map(str, [walk, pct, fdw])
	def GET(self):
		timings = []
		lag = []
		int_id = web.input().IntID
		kwargs = db.get_info(int_id)
		for index in range(num_phases):
			yar_length = kwargs['yar_len'].split(';')[index]
			fdw_length = kwargs['fdw_len'].split(';')[index]
			speed = kwargs['speed'].split(';')[index]
			grade = kwargs['grade'].split(';')[index]
			mov = kwargs['mov'].split(';')[index]
			adj = kwargs['lag'].split(';')[index]
			if adj:
				lag.append([index, int(adj) - 1])

			yar_length = int(yar_length or 0)
			fdw_length = int(fdw_length or 0)
			speed = int(speed or 0)
			grade = float(grade or 0)

			yellow, red = self.calcYAR(yar_length, speed, grade, mov)
			walk, pct, fdw = self.calcPed(fdw_length, red, yellow)
			
			timings.append([yellow, red, walk, pct, fdw])

		for index, adj in lag:
			yellow = max(timings[index][0], timings[adj][0])
			red = max(timings[index][1], timings[adj][1])
			walk = max(timings[index][2], timings[adj][2])
			pct  = max(timings[index][3], timings[adj][3])
			fdw = max(timings[index][4], timings[adj][4])
			timings[index] = [yellow, red, walk, pct, fdw]
			timings[adj] = [yellow, red, walk, pct, fdw]

		render = web.template.render('templates')
		return render.output(kwargs, timings)

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
