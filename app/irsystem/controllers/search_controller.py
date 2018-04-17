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
		default, reviews = gen_data()
		query['trail'] = None #request.form['trail_name']
	  	query['keywords'] = {request.form['keyword'].encode('ascii', 'ignore'):1}
	  	#query['distance'] = request.form['distance']
	  	#query['city'] = request.form['city']
	  	#query['state'] = request.form['state']
	  	#query['start_altitude'] = [request.form['start_altitude_lb'], request.form['start_altitude_ub']]
	  	#print(query)
	  	ranking = handle_query(query, default, reviews)
		return redirect(url_for('irsystem.result', r1=ranking[0]))
	else:
		return render_template('search.html')



@irsystem.route('irsystem.result', methods=["GET","POST"])
def result():
	r1 = request.args.get('r1')
	return 'This is the result page. Trail ID is: ' + str(r1)