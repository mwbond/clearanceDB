import sqlite3
conn = sqlite3.connect('intersection_db')
c = conn.cursor()
c.execute('''create table intersection
			(int_id text, location text default '', map_lat text default '', map_lng text default '', map_zoom text default '', major text default '', minor text default '',
			p1_yar_lat1 default '', p1_yar_lng1 default '', p1_fdw_lat1 default '', p1_fdw_lng1 default '',
			p1_yar_lat2 default '', p1_yar_lng2 default '', p1_fdw_lat2 default '', p1_fdw_lng2 default '',
			p2_yar_lat1 default '', p2_yar_lng1 default '', p2_fdw_lat1 default '', p2_fdw_lng1 default '',
			p2_yar_lat2 default '', p2_yar_lng2 default '', p2_fdw_lat2 default '', p2_fdw_lng2 default '',
			p3_yar_lat1 default '', p3_yar_lng1 default '', p3_fdw_lat1 default '', p3_fdw_lng1 default '',
			p3_yar_lat2 default '', p3_yar_lng2 default '', p3_fdw_lat2 default '', p3_fdw_lng2 default '',
			p4_yar_lat1 default '', p4_yar_lng1 default '', p4_fdw_lat1 default '', p4_fdw_lng1 default '',
			p4_yar_lat2 default '', p4_yar_lng2 default '', p4_fdw_lat2 default '', p4_fdw_lng2 default '',
			p5_yar_lat1 default '', p5_yar_lng1 default '', p5_fdw_lat1 default '', p5_fdw_lng1 default '',
			p5_yar_lat2 default '', p5_yar_lng2 default '', p5_fdw_lat2 default '', p5_fdw_lng2 default '',
			p6_yar_lat1 default '', p6_yar_lng1 default '', p6_fdw_lat1 default '', p6_fdw_lng1 default '',
			p6_yar_lat2 default '', p6_yar_lng2 default '', p6_fdw_lat2 default '', p6_fdw_lng2 default '',
			p7_yar_lat1 default '', p7_yar_lng1 default '', p7_fdw_lat1 default '', p7_fdw_lng1 default '',
			p7_yar_lat2 default '', p7_yar_lng2 default '', p7_fdw_lat2 default '', p7_fdw_lng2 default '',
			p8_yar_lat1 default '', p8_yar_lng1 default '', p8_fdw_lat1 default '', p8_fdw_lng1 default '',
			p8_yar_lat2 default '', p8_yar_lng2 default '', p8_fdw_lat2 default '', p8_fdw_lng2 default '')''')
conn.commit()
c.close()
