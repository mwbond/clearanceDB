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
		reader = csv.reader(cStringIO.StringIO(layout_txt))
		nodes, lanes, links, phases = {}, {}, {}, {}
		heading = ''
		dirs = []
		phase_headings = []
		for row in reader:
			try:
				if len(row)==0:
					heading = ''
				elif '[' in row[0]:
					heading = row[0][1:-1]
				elif heading=='Nodes' and row[1]=='0':
					nodes[row[0]] = {'int_id': row[0]}
					lanes[row[0]] = [''] * 4
				elif heading=='Links':
					if row[0]=='RECORDNAME':
						dirs = row[2:]
					elif row[0]=='Name' and row[1] in nodes.keys():
						names = row[2:]
						names.extend(['']*(len(dirs)-len(names)))
						links[row[1]] = dict(zip(dirs, names))
						names = list(set(names))
						if '' in names:
							names.remove('')
						if len(names) > 1:
							nodes[row[1]]['minor'] = names[1]
						if len(names) > 0:
							nodes[row[1]]['major'] = names[0]
				elif heading=='Lanes':
					if row[0]=='RECORDNAME':
						dirs = [dir for dir in row[2:] if dir[0] in ['N', 'S', 'E', 'W']]
					if row[1] not in lanes.keys():
						continue
					if row[0]=='Speed':
						lanes[row[1]][0] = row[2:][:len(dirs)]
					elif row[0]=='Grade':
						lanes[row[1]][1] = row[2:][:len(dirs)]
					elif row[0]=='Phase1':
						lanes[row[1]][2] = row[2:][:len(dirs)]
					elif row[0]=='Peds':
						lanes[row[1]][3] = row[2:][:len(dirs)]
				'''elif heading=='Phases':
					if row[0]=='RECORDNAME':
						phase_headings = [p[1:] for p in row[2:]]
					elif row[0]=='BRP':
						phases[row[1]] = row[2:][:phase_headings]'''
			except IndexError:
				pass
		for key in nodes.keys():
			phase_info = [[''] * num_phases,
						[''] * num_phases,
						[''] * num_phases,
						[''] * num_phases,
						[''] * num_phases,
						[''] * num_phases]
			speeds, grades, phases, peds = lanes[key]
			speeds.extend(['']*(len(phases)-len(speeds)))
			grades.extend(['']*(len(phases)-len(grades)))
			peds.extend(['']*(len(phases)-len(peds)))
			for index in range(len(phases)):
				phase = phases[index]
				if phase=='':
					continue
				mov = ''
				speed = speeds[index] or '0'
				if 'L' in dirs[index]:
					mov = 'on'
					speed = '20'
				grade = grades[index] or '0'
				ped = peds[index] or '0'
				if int(ped) < 1000:
					walk = '7'
				else:
					walk = '10'
				phase = int(phase)
				try:
					phase_info[0][phase - 1] = speed
					phase_info[1][phase - 1] = grade
					phase_info[2][phase - 1] = walk
					phase_info[3][phase - 1] = dirs[index]
					phase_info[4][phase - 1] = mov
					if dirs[index][:2] in links[key].keys():
						phase_info[5][phase - 1] = links[key][dirs[index][:2]]

				except IndexError:
					pass
			nodes[key]['speed'] = ';'.join(phase_info[0])
			nodes[key]['grade'] = ';'.join(phase_info[1])
			nodes[key]['min_walk'] = ';'.join(phase_info[2])
			nodes[key]['dir'] = ';'.join(phase_info[3])
			nodes[key]['mov'] = ';'.join(phase_info[4])
			nodes[key]['road'] = ';'.join(phase_info[5])
			db.modify(**nodes[key])
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
		location = db.get_info()['location']
		print kwargs
		render = web.template.render('templates', globals={'map': map, 'str': str, 'zip': zip})
		return render.intersection(kwargs, location)

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
	def calcYAR(self, kwargs):
		end = []
		timings = []
		yar_len = kwargs['yar_len'].split(';')
		speeds = kwargs['speed'].split(';')
		grades = kwargs['grade'].split(';')
		movements = kwargs['mov'].split(';')
		adjacents = kwargs['end'].split(';')
		int_controlled = kwargs['int_controlled']
		for index in range(num_phases):
			length = int(yar_len[index] or 0)
			speed = int(speeds[index] or 0)
			grade = float(grades[index] or 0)
			turn = movements[index]
			adj = adjacents[index]
			if adj:
				end.append([index, int(adj) - 1])

			div = 2.0
			if int_controlled:
				div = 1.0
			if (length==0) or (speed==0):
				timings.append(['-', '-', '', '', ''])
				continue
			if turn:
				min_r = 0.5
				y_speed = 20.0
				r_speed = 1.47 * 20.0
			else:
				min_r = 1.0
				y_speed = speed + 5.0
				r_speed = 1.47 * speed

			yellow_c = 1 + (0.733 * y_speed)/(10.0 + (0.32 * grade))
			yellow_r = ceil(div * yellow_c)/div
			yellow_c = round(yellow_c, 1)
			red_c = length / r_speed
			red_r = ceil(div * red_c) / div
			red_c = round(red_c, 1)

			yellow_r = min(yellow_r, 6)
			yellow_r = max(yellow_r, 4)
			red_r = min(red_r, 3)
			red_r = max(red_r, min_r)
			diff = yellow_c + red_c - yellow_r - red_r
			diff = ceil(div * diff) / div
			if diff > 0:
				yellow_r = yellow_r + diff
			yellow = str(yellow_r / 1.0)
			red = str(red_r / 1.0)
			timings.append([yellow, red, '', '', ''])

		for index, adj in end:
			y1, r1 = timings[index][:2]
			y2, r2 = timings[adj][:2]
			if y1 != '-' and y2 != '-':
				timings[index][:2] = max(y1, y2), max(r1, r2)
				timings[adj][:2] = max(y1, y2), max(r1, r2)
		return timings
	def calcPed(self, kwargs, timings):
		fdw_len = kwargs['fdw_len'].split(';')
		min_walks = kwargs['min_walk'].split(';')
		for index in range(num_phases):
			yellow, red = timings[index][:2]
			length = int(fdw_len[index] or 0)
			min_walk = float(min_walks[index] or 7)
			if length==0:
				timings[index][2:] = '-', '-', '-'
				continue
			if red=='-':
				red = 0
			if yellow=='-':
				yellow = 0
			pct = length / 3.5
			walk = round(max((length + 6) / 3.0 - pct, min_walk))
			fdw = pct - float(yellow) - float(red)
			pct = round(pct)
			fdw = round(max(4.0, fdw))
			timings[index][2:] = walk, pct, fdw
	def GET(self):
		int_id = web.input().IntID
		kwargs = db.get_info(int_id)
		timings = self.calcYAR(kwargs)
		self.calcPed(kwargs, timings)
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
