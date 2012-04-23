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
		int_info = {}
		heading = ''
		dirs = []
		roads = {}
		len_dirs = 0
		for row in reader:
			if len(row)==0:
				heading = ''
				continue
			if '[' in row[0]:
				heading = row[0][1:-1]
				continue
			try:
				if heading=='Nodes' and row[1]=='0':
					int_info[row[0]] = {'int_id': row[0], 'lanes': [[], [], [], []]}
				elif heading=='Links':
					if row[0]=='RECORDNAME':
						dirs = row[2:]
					elif row[0]=='Name' and row[1] in int_info.keys():
						names = row[2:]
						names.extend(['']*(len(dirs)-len(names)))
						roads[row[1]] = dict(zip(dirs, names))
						names = list(set(names))
						if '' in names:
							names.remove('')
						if len(names) > 1:
							int_info[row[1]]['minor'] = names[1]
						if len(names) > 0:
							int_info[row[1]]['major'] = names[0]
				elif heading=='Lanes':
					if row[0]=='RECORDNAME':
						dirs = [dir for dir in row[2:] if dir[0] in ['N', 'S', 'E', 'W']]
						len_dirs = len(dirs)
					if row[1] not in int_info.keys():
						continue
					if row[0]=='Speed':
						int_info[row[1]]['lanes'][0] = row[2:][:len_dirs]
					elif row[0]=='Grade':
						int_info[row[1]]['lanes'][1] = row[2:][:len_dirs]
					elif row[0]=='Phase1':
						int_info[row[1]]['lanes'][2] = row[2:][:len_dirs]
					elif row[0]=='Peds':
						int_info[row[1]]['lanes'][3] = row[2:][:len_dirs]
			except IndexError:
				pass
		for key in int_info.keys():
			phase_info = [[''] * num_phases,
						[''] * num_phases,
						[''] * num_phases,
						[''] * num_phases,
						[''] * num_phases,
						[''] * num_phases]
			lanes = int_info[key].pop('lanes')
			speeds, grades, phases, peds = lanes
			speeds.extend(['']*(len(phases)-len(speeds)))
			grades.extend(['']*(len(phases)-len(grades)))
			peds.extend(['']*(len(phases)-len(peds)))
			for index in range(len(phases)):
				mov = ''
				phase = phases[index]
				if phase=='':
					continue
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
					if dirs[index][:2] in roads[key].keys():
						phase_info[5][phase - 1] = roads[key][dirs[index][:2]]

				except IndexError:
					pass
			int_info[key]['speed'] = ';'.join(phase_info[0])
			int_info[key]['grade'] = ';'.join(phase_info[1])
			int_info[key]['min_walk'] = ';'.join(phase_info[2])
			int_info[key]['dir'] = ';'.join(phase_info[3])
			int_info[key]['mov'] = ';'.join(phase_info[4])
			int_info[key]['road'] = ';'.join(phase_info[5])
			db.modify(**int_info[key])
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
		#DEFAULTS
		if not kwargs['map_lat']:
			kwargs['map_lat'] = '39.26'
			kwargs['map_lng'] = '-76.67'
		if not kwargs['map_zoom']:
			kwargs['map_zoom'] = '18'

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
