import os
import sqlite3
import web

num_phases = 8

if not os.path.isfile('intersection_db'):
	default = "'" + (num_phases - 1) * ';' + "'"
	conn = sqlite3.connect('intersection_db')
	c = conn.cursor()
	command = '''create table intersection
				(int_id text,
				location text default '',
				map_lat text default '',
				map_lng text default '',
				map_zoom text default '',
				major text default '',
				minor text default '',
				int_controlled text default '',
				yar_line default $,
				fdw_line default $,
				mov default $,
				road default $,
				grade default $,
				speed default $,
				dir default $,
				yar_len default $,
				fdw_len default $,
				min_walk default $,
				end default $)'''
	c.execute(command.replace('$', default))
	conn.commit()
	c.close()

DB = web.database(dbn='sqlite', db='intersection_db')

# Returns number of entries with int_id
def entry_exists(int_id='0'):
	query_cmd = 'SELECT COUNT(*) AS id_matches FROM intersection WHERE int_id=$int_id'
	results = DB.query(query_cmd, vars={'int_id':int_id})	
	return results[0].id_matches

# Return list of (Intersection ID, Intersection Name) in ascending order
# If no major or minor road names are stored, 'Unknown' is subsituted 
def get_db_info():
	db_info = []
	results = DB.select('intersection', where='int_id<>0', order='int_id ASC')
	for entry in results:
		if entry['major'] or entry['minor']:
			int_name =  entry['major'] + ' and ' + entry['minor']
			db_info.append((entry['int_id'], int_name))
		else:
			db_info.append((entry['int_id'], 'Unkown'))
	return db_info

# Deletes entry if Intersection ID is in DB
def delete_id(int_id):
	if entry_exists(int_id):
		DB.delete('intersection', where="int_id=$int_id", vars={'int_id':int_id})

# Returns dictionary of values for the entry with the Intersection ID
# If the int_id is not in the DB and the int_id is '0' then it is 
# inserted into the DB
def get_info(int_id='0'):
	if not entry_exists(int_id):
		if int_id=='0':
			DB.insert('intersection', int_id='0')
	results = DB.select('intersection', where='int_id=$int_id', vars={'int_id':int_id})
	return dict(results[0])

# Edits existing entries if ID is in DB, otherwise creates an entry
# with the default location. If no ID is given, the location is changed for the
# entire DB
def modify(**kwargs):
	try:
		if 'int_id' in kwargs:
			int_id = kwargs.pop('int_id')
			if entry_exists(int_id):
				DB.update('intersection', where='int_id=$int_id', vars={'int_id':int_id}, **kwargs)
			else:
				loc = get_info()['location']
				kwargs.update({'int_id':int_id, 'location':loc})
				DB.insert('intersection', **kwargs)
		elif 'location' in kwargs:
			DB.update('intersection', where='1=1', location=kwargs['location'])
	except TypeError:
		print('Object passed to db.modify was not **dict')
	except sqlite3.OperationalError:
		print('Dictionary passed to db.modify had a key that was not a column in the DB')
