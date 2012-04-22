import sqlite3
num_phases = 8
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
			yar_line default $,
			fdw_line default $,
			mov default $,
			road default $,
			grade default $,
			speed default $,
			dir default $,
			yar_len default $,
			fdw_len default $,
			lag default $)'''

c.execute(command.replace('$', default))
conn.commit()
c.close()
