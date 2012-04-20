import sqlite3
conn = sqlite3.connect('intersection_db')
c = conn.cursor()
c.execute('''create table intersection
			(int_id text, location text default '', map_lat text default '', map_lng text default '', map_zoom text default '', major text default '', minor text default '',
			p1_yar_line default '', p1_fdw_line default '', p1_mov default '', p1_road default '', p1_grade default '', p1_speed default '', p1_dir default '', p1_yar_len default '', p1_fdw_len default '', p1_y default '', p1_r default '', p1_f default '', p1_lag default '',
			p2_yar_line default '', p2_fdw_line default '', p2_mov default '', p2_road default '', p2_grade default '', p2_speed default '', p2_dir default '', p2_yar_len default '', p2_fdw_len default '', p2_y default '', p2_r default '', p2_f default '', p2_lag default '',
			p3_yar_line default '', p3_fdw_line default '', p3_mov default '', p3_road default '', p3_grade default '', p3_speed default '', p3_dir default '', p3_yar_len default '', p3_fdw_len default '', p3_y default '', p3_r default '', p3_f default '', p3_lag default '',
			p4_yar_line default '', p4_fdw_line default '', p4_mov default '', p4_road default '', p4_grade default '', p4_speed default '', p4_dir default '', p4_yar_len default '', p4_fdw_len default '', p4_y default '', p4_r default '', p4_f default '', p4_lag default '',
			p5_yar_line default '', p5_fdw_line default '', p5_mov default '', p5_road default '', p5_grade default '', p5_speed default '', p5_dir default '', p5_yar_len default '', p5_fdw_len default '', p5_y default '', p5_r default '', p5_f default '', p5_lag default '',
			p6_yar_line default '', p6_fdw_line default '', p6_mov default '', p6_road default '', p6_grade default '', p6_speed default '', p6_dir default '', p6_yar_len default '', p6_fdw_len default '', p6_y default '', p6_r default '', p6_f default '', p6_lag default '',
			p7_yar_line default '', p7_fdw_line default '', p7_mov default '', p7_road default '', p7_grade default '', p7_speed default '', p7_dir default '', p7_yar_len default '', p7_fdw_len default '', p7_y default '', p7_r default '', p7_f default '', p7_lag default '',
			p8_yar_line default '', p8_fdw_line default '', p8_mov default '', p8_road default '', p8_grade default '', p8_speed default '', p8_dir default '', p8_yar_len default '', p8_fdw_len default '', p8_y default '', p8_r default '', p8_f default '', p8_lag default '')''')
conn.commit()
c.close()
