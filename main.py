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
		for row in reader:
			try:
				if len(row)==0:
					heading = ''
				elif '[' in row[0]:
					heading = row[0][1:-1]
				elif heading=='Nodes' and row[1]=='0':
					nodes[row[0]] = {'int_id': row[0]}
					links[row[0]] = []
					lanes[row[0]] = {'speed': [], 'grade': [], 'phase': [], 'peds': []}
					phases[row[0]] = []
				elif heading=='Links':
					if row[0]=='RECORDNAME':
						links['col'] = row[2:]
					elif row[0]=='Name' and row[1] in nodes.keys():
						links[row[1]] = row[2:]
				elif heading=='Lanes':
					if row[0]=='RECORDNAME':
						lanes['col'] = row[2:]
					elif row[1] not in lanes.keys():
						continue
					elif row[0]=='Speed':
						lanes[row[1]]['speed'] = row[2:]
					elif row[0]=='Grade':
						lanes[row[1]]['grade'] = row[2:]
					elif row[0]=='Phase1':
						lanes[row[1]]['phase'] = row[2:]
					elif row[0]=='Peds':
						lanes[row[1]]['peds'] = row[2:]
				elif heading=='Phases':
					if row[0]=='RECORDNAME':
						phases['col'] = [p[1:] for p in row[2:]]
					elif row[0]=='BRP' and row[1] in phases.keys():
						phases[row[1]] = row[2:]
			except IndexError:
				pass
		lanes_mod = {}
		for int_id in nodes.keys():
			if int_id == 'col':
				continue
			matrix = []
			str_phases = map(str, range(1, num_phases + 1))
			brp = list(set(phases[int_id]))
			if '' in brp:
				brp.remove('')
			brp.sort()
			maxes, phase_maxes = [], []
			for index in range(len(brp)):
				if len(brp) == index + 1:
					maxes.append(brp[index])
				elif brp[index][:2] != brp[index + 1][:2]:
					maxes.append(brp[index])
			for index in range(len(maxes)):
				phase = phases['col'][phases[int_id].index(maxes[index])]
				if phase in lanes[int_id]['phase']:
					phase_maxes.append(phase)
				else:
					phase_maxes.append('')

			for index in range(len(lanes[int_id]['phase'])):
				phase = lanes[int_id]['phase'][index]
				dirs = lanes['col'][index]
				speed = lanes[int_id]['speed'][index]
				grade = lanes[int_id]['grade'][index]
				peds = lanes[int_id]['peds'][index]
				mov = ''
				speed = speed or '0'
				grade = grade or '0'
				if 'L' in dirs:
					mov = 'on'
					speed = '20'
				peds = peds or '10'
				if int(peds) < 1000:
					walk = '7'
				if dirs[:2] in links['col']:
					i = links['col'].index(dirs[:2])
					road = links[int_id][i]
				else:
					road = ''
				end = []
				if phase in phase_maxes:
					barrier = maxes[phase_maxes.index(phase)][0]
					print barrier
					for brp in maxes:
						if brp[0] == barrier:
							p = phase_maxes[maxes.index(brp)]
							if p and p != phase and int(p) > 0 and int(p) <= num_phases:
								end.append(p)
				end = ','.join(end)

				if phase in str_phases:
					matrix.append([phase, dirs, speed, grade, peds, mov, road, end])
					str_phases.pop(str_phases.index(phase))
			for phase in str_phases:
				matrix.append([phase] + [''] * 7)
			matrix.sort(key=lambda x: x[0])
			lanes_mod[int_id] = zip(*matrix)

		for int_id in nodes.keys():
			nodes[int_id]['dir'] = ';'.join(lanes_mod[int_id][1])
			nodes[int_id]['speed'] = ';'.join(lanes_mod[int_id][2])
			nodes[int_id]['grade'] = ';'.join(lanes_mod[int_id][3])
			nodes[int_id]['min_walk'] = ';'.join(lanes_mod[int_id][4])
			nodes[int_id]['mov'] = ';'.join(lanes_mod[int_id][5])
			nodes[int_id]['road'] = ';'.join(lanes_mod[int_id][6])
			nodes[int_id]['end'] = ';'.join(lanes_mod[int_id][7])

			names = list(set(links[int_id]))
			if '' in names:
				names.remove('')
				if len(names) > 1:
					nodes[int_id]['minor'] = names[1]
				if len(names) > 0:
					nodes[int_id]['major'] = names[0]
			db.modify(**nodes[int_id])
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
		timings = []
		yar_len = kwargs['yar_len'].split(';')
		speeds = kwargs['speed'].split(';')
		grades = kwargs['grade'].split(';')
		movements = kwargs['mov'].split(';')
		end = kwargs['end'].split(';')
		int_controlled = kwargs['int_controlled']
		for index in range(num_phases):
			length = int(yar_len[index] or 0)
			speed = int(speeds[index] or 0)
			grade = float(grades[index] or 0)
			turn = movements[index]

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

		for index in range(num_phases):
			if end[index]:
				ends_with = [index]
				y = [timings[index][0]]
				r = [timings[index][1]]
				for phase in end[index].split(','):
					p = int(phase) - 1
					if timings[int(phase) - 1][0] != '-':
						y.append(timings[p - 1][0])
						r.append(timings[p - 1][1])
						ends_with.append(p - 1)
				max_y = max(y)
				max_r = max(r)
				for index in ends_with:
					timings[index][:2] = max_y, max_r
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
