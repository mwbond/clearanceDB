import csv
import cStringIO
import web

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
