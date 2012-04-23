import csv

num_phases = 8

reader = csv.reader(open('ward1plan1.csv', 'r'))

int_info = {}
heading = ''
dirs = []
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
			if row[0]=='Name' and row[1] in int_info.keys():
				names = list(set(row[2:]))
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
	phase_info = [[''] * num_phases, [''] * num_phases, [''] * num_phases, [''] * num_phases]
	lanes = int_info[key].pop('lanes')
	speeds, grades, phases, peds = lanes
	speeds.extend(['']*(len(phases)-len(speeds)))
	grades.extend(['']*(len(phases)-len(grades)))
	peds.extend(['']*(len(phases)-len(peds)))
	for index in range(len(phases)):
		phase = phases[index]
		if phase=='':
			continue
		speed = speeds[index] or '0'
		if 'T' in dirs[index]:
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
		except IndexError:
			pass
	int_info[key]['speed'] = ','.join(phase_info[0])
	int_info[key]['grade'] = ','.join(phase_info[1])
	int_info[key]['min_walk'] = ','.join(phase_info[2])
	int_info[key]['dir'] = ','.join(phase_info[3])
