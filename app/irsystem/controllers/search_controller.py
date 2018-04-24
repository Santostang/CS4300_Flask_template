from . import *  
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
from app.irsystem.models.search import handle_query, gen_data, clean
import re
project_name = "Ilan's Cool Project Template"
net_id = "Ilan Filonenko: if56"

@irsystem.route('/', methods=['GET', 'POST'])
def search():
	query = {}
	if request.method == "POST":
		default, reviews,_ = gen_data()
		query['trail'] = None
		#query['trail'] = request.form['trail_name']
		if request.form['trail_name'] != '':
			f = re.compile(request.form['trail_name'])
			for t in default:
				if f.search(t['trail_name']):
					query['trail'] = t
					print('found')
					break
		kwds = {}
		for word in clean(request.form['keywords'].encode('ascii', 'ignore')):
			if word not in kwds:
				kwds[word] = 0
			kwds[word] += 1
		if len(kwds) > 0:
			query['keywords'] = kwds
		else:
			query['keywords'] = None
	  	#query['keywords'] = {request.form['keywords'].encode('ascii', 'ignore'):1}
	  	#query['distance'] = request.form['distance']
	  	#query['city'] = request.form['city']
	  	if request.form['near'] != '':
	  		query['state'] = request.form['near']
	  		print(query['state'])
	  	#query['start_altitude'] = [request.form['start_altitude_lb'], request.form['start_altitude_ub']]
	  	#print(query)
	  	ranking = handle_query(query, default, reviews)
		results = {'r' + str(k):ranking[k]['trail_id'] for k in range(10)}
		print(ranking[0])
		return redirect(url_for('irsystem.result',**results))
	else:
		default, reviews,_ = gen_data()
		return render_template('search.html')



@irsystem.route('irsystem.result', methods=["GET","POST"])
def result():
	query = {}
	print("great")
	if request.method == "POST":
		query['distance'] = {request.form['distance'].encode('ascii', 'ignore')}
	_, _, trails = gen_data()
	dat = []
	for k in ['r0','r1','r2','r3','r4','r5','r6','r7','r8','r9']:
    		dat.append(trails[request.args.get(k)])
	return render_template('result2.html', data = dat)