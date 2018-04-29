from . import *  
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
from app.irsystem.models.search import handle_query, gen_data, clean
import re
project_name = "Ilan's Cool Project Template"
net_id = "Ilan Filonenko: if56"

def get_results(query, default, reviews, svds, keyword):
	ranking = handle_query(query, default, reviews, svds)
	results = {}
	for k in range(10):
		if k >= len(ranking):
			results['r'+str(k)] = "NILL"
		else:
			results['r'+str(k)] = ranking[k]['trail_id']
	results['found'] = len(ranking)
	results['display'] = min(10,len(ranking))
	if 'trail' in query:
		results['trail_name'] = query['trail']['trail_name']
	else:
		results['trail_name'] = None
	results['keywords'] = keyword
	if 'state' in query:
		results['state'] = query['state'].encode('ascii', 'ignore')
	else:
		results['state'] = None
	return results

@irsystem.route('/', methods=['GET', 'POST'])
def search():
	query = {}
	if request.method == "POST":
		default, reviews,_,svds = gen_data()
		query['trail'] = None
		#query['trail'] = request.form['trail_name']
		if request.form['trail_name'] != '':
			#query['trail'] = request.form['trail_name'].encode('ascii', 'ignore')
			f = re.compile(request.form['trail_name'].encode('ascii', 'ignore'))
			for t in default:
				if f.search(t['trail_name']):
					query['trail'] = t
					print('found')
					break
		keyword = request.form['keywords']
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
	  		query['state'] = request.form['near'].encode('ascii', 'ignore')
	  	#query['start_altitude'] = [request.form['start_altitude_lb'], request.form['start_altitude_ub']]
		results = get_results(query,default,reviews,svds,keyword)
		#results = {('r' + str(k):ranking[k]['trail_id']) if k < len(ranking) else ('r'+str(k):None) for k in range(10)}
		print(results)
		return redirect(url_for('irsystem.result',**results))
	else:
		default, reviews,_,_ = gen_data()
		return render_template('search.html')



@irsystem.route('irsystem.result', methods=["GET","POST"])
def result():
	query = {}
	default, reviews,trails,svds = gen_data()
	if request.method == "POST":
		query = {}
		if request.args.get('trail_name') is not None:
			query['trail'] = request.args.get('trail_name').encode('ascii', 'ignore')
			f = re.compile(request.args.get('trail_name').encode('ascii', 'ignore'))
			for t in default:
				if f.search(t['trail_name']):
					query['trail'] = t
					break
		else:
			query['trail'] = None
		keyword = request.args.get('keywords')
		if request.args.get('keywords') is not None:
			kwds = {}
			for word in clean(request.args.get('keywords').encode('ascii', 'ignore')):
				if word not in kwds:
					kwds[word] = 0
				kwds[word] += 1
			if len(kwds) > 0:
				query['keywords'] = kwds
			else:
				query['keywords'] = None
		if request.args.get('state') is not None:
			query['state'] = request.args.get('state').encode('ascii', 'ignore')

		if request.form['distance'] != '':
			query['length'] = request.form['distance'].encode('ascii', 'ignore')

		if request.form['elevation_gain'] != '':
			query['change_altitude'] = request.form['elevation_gain'].encode('ascii', 'ignore')
		
		if request.form.get("route_type") is not None or request.form.get("route_type") != '':
			query['routetypes'] = request.form["route_type"].encode('ascii', 'ignore')

		if request.form.get("activities") is not None or request.form.get("activities") != '':
			query['tags'] = request.form["activities"].encode('ascii', 'ignore')

		print(query)
		results = get_results(query,default,reviews,svds,keyword)
		dat = [results['found'],results['display']]
		for k in ['r0','r1','r2','r3','r4','r5','r6','r7','r8','r9']:
    			print(results[k])
    			if results[k] in trails:
		    		dat.append(trails[results[k]])
		return render_template('result2.html', data = dat)
	else:
		dat = [request.args.get('found'),request.args.get('display')]
		for k in ['r0','r1','r2','r3','r4','r5','r6','r7','r8','r9']:
    			print(request.args.get(k))
    			if request.args.get(k) in trails:
		    		dat.append(trails[request.args.get(k)])
		print(dat)
		return render_template('result2.html', data = dat)


