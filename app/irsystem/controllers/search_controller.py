from . import *  
from app.irsystem.models.helpers import *
from app.irsystem.models.helpers import NumpyEncoder as NumpyEncoder
from app.irsystem.models.search import handle_query, gen_data
project_name = "Ilan's Cool Project Template"
net_id = "Ilan Filonenko: if56"

@irsystem.route('/', methods=['GET', 'POST'])
def search():
	query = {}
	if request.method == "POST":
		default, reviews,_ = gen_data()
		query['trail'] = None #request.form['trail_name']
	  	query['keywords'] = {request.form['keywords'].encode('ascii', 'ignore'):1}
	  	#query['distance'] = request.form['distance']
	  	#query['city'] = request.form['city']
	  	#query['state'] = request.form['state']
	  	#query['start_altitude'] = [request.form['start_altitude_lb'], request.form['start_altitude_ub']]
	  	#print(query)
	  	ranking = handle_query(query, default, reviews)
		results = {'r' + str(k):ranking[k]['trail_id'] for k in range(10)}
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