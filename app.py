from app import app, socketio
from flask import Flask, request, render_template, url_for, redirect

import os, csv, math, re
import pprint
from math import radians, cos, sin, asin, sqrt

#@app.route('/', methods=["GET","POST"])
def search():
	query = {}
	if request.method == "POST":
            query['trail'] =  request.form['trail_name']

            query['keywords'] = {request.form['keyword'].encode('ascii', 'ignore'):1}

            #query['distance'] = request.form['distance']
            #query['city'] = request.form['city']
            #query['state'] = request.form['state']
            #query['start_altitude'] = [request.form['start_altitude_lb'], request.form['start_altitude_ub']]
            ranking = handle_query(query, default, reviews)
            return render_template('search.html', data=ranking[:2])
            #return redirect(url_for('result', r1=ranking[0]))

#@app.route('/result', methods=["GET","POST"])
def result():
	r1 = request.args.get('r1')
	return 'This is the result page. Trail ID is: ' + str(r1)


def load_data():
    """

    :return:
    """
    trail = {}
    reader = csv.DictReader(open('trail_info.csv', 'rb'))
    for line in reader:
        trail[line['trail_id']] = line
    return trail


def clean(string):
    return re.compile("\w+").findall(string.lower())


def load_reviews():
    reviews = {'all': set([])}
    reader1 = csv.DictReader(open('review1.csv', 'rb'))
    for line in reader1:
        if '' == line['comment']:
            continue
        tid = line['trail_id']
        if tid not in reviews:
            reviews[tid] = ({}, 0)
        reviews[tid] = (reviews[tid][0], reviews[tid][1] + 1)
        for wrd in clean(line['comment']):
            if wrd not in reviews[tid][0]:
                reviews[tid][0][wrd] = 0
            reviews[tid][0][wrd] += 1
            reviews['all'].add(wrd)

    reader2 = csv.DictReader(open('review2.csv', 'rb'))
    for line in reader2:
        if '' == line['comment']:
            continue
        tid = line['trail_id']
        if tid not in reviews:
            reviews[tid] = ({}, 0)
        reviews[tid] = (reviews[tid][0], reviews[tid][1] + 1)
        for wrd in clean(line['comment']):
            if wrd not in reviews[tid][0]:
                reviews[tid][0][wrd] = 0
            reviews[tid][0][wrd] += 1
            reviews['all'].add(wrd)
    return reviews


def score_trail(trail_id, trail):
    """

    :param trail_id:
    :return:
    """
    if trail['avgRating'] is None or trail['avgRating'] == '':
        return trail, 0
    score = float(trail['avgRating']) * math.log(int(trail['reviewCount']))
    return trail, score


def calc_default(trails):
    """

    :return:
    """
    scored = [score_trail(tid, tr) for tid, tr in trails.items()]
    sort = sorted(scored, key=lambda tup: tup[1], reverse=True)
    return [i[0] for i in sort]


def handle_query(query, default_ranking,reviews):
    """
    :param query:
    :return:
    """
    valid = default_ranking
    if 'length' in query:
        valid = filter_length(valid, query['length'])
    if 'distance' in query:
        valid = filter_distance(valid, query['distance'])
    if 'difficulty' in query:
        valid = filter_difficulty(valid, query['difficulty'])
    if 'start_altitude' in query:
        valid = filter_start_altitude(valid, query['elevationStart'])
    if 'max_altitude' in query:
        valid = filter_max_altitude(valid, query['elevationMax'])
    if 'change_altitude' in query:
        valid = filter_change_altitude(valid, query['elevationGain'])
    if 'tags' in query:
        valid = filter_tags(valid, query['tags'])
    if 'routetypes' in query:
        valid = filter_routetypes(valid, query['routetypes'])
    if 'states' in query:
        valid = filter_states(valid, query['states'])
    ranking = make_ranking(valid, query['trail'], query['keywords'],reviews)
    return ranking


def calc_keyword_similarity(valid, keywords, reviews):
    def score(twords, kwords):
        dot = sum([kwords[w]*twords[0][w] for w in kwords if w in twords[0]]) / twords[1]
        tmag = math.sqrt(sum([twords[0][w]*twords[0][w] for w in twords[0]]))
        kmag = math.sqrt(sum([kwords[w]*kwords[w] for w in kwords]))
        return dot / (tmag * kmag)
    tmp = [(t, score(reviews[t['trail_id']],keywords)) if t['trail_id'] in reviews else (t,0)
                for t in valid]
    m = max(tmp, key=lambda l: l[1])
    return [(a,b/m[1]) for (a,b) in tmp]


def calc_trail_similarity(valid, trail, reviews):
    def score_rev(twords, kwords):
        dot = sum([kwords[0][w]*twords[0][w] for w in kwords[0] if w in twords[0]]) / twords[1] / kwords[1]
        tmag = math.sqrt(sum([twords[0][w]*twords[0][w] for w in twords[0]]))
        kmag = math.sqrt(sum([kwords[0][w]*kwords[0][w] for w in kwords[0]]))
        return dot / (tmag * kmag)
    def score_trail(t, v):
        dot = 0
        magT = 0
        magV = 0
        for f,func in [('avgRating',float), ('difficulty',int), ('duration',int), \
                    ('elevationGain',float), ('elevationMax',float), ('elevationStart',float), ('length',float)]:
            if f not in t or f not in v:
                continue
            if t[f] is None or v[f] is None:
                continue
            dot = dot + (func(t[f]) / func(v[f]) if func(t[f]) < func(v[f]) else func(v[f]) / func(t[f]))
            magT = magT + func(t[f]) ** 2
            magV = magV + func(v[f]) ** 2
        for f,fields in [
                ('activities',
                    ['Snowshoeing', 'Surfing', 'Cross Country Skiing', 'Fishing', 'Horseback Riding', 'Scenic Driving',
                    'Off Road Driving', 'Skiing', 'Paddle Sports', 'Walking', 'Hiking', 'Camping', 'Mountain Biking',
                    'Birding', 'Trail Running', 'Backpacking', 'Road Biking', 'Rock Climbing', 'Nature Trips']),
                ('features',
                     ['Waterfall', 'Cave', 'Kids', 'Dogs', 'City Walk', 'Dogs Leash', 'Dogs No', 'Historic Site', 
                     'Rails Trails', 'Views', 'Wild Flowers', 'Lake', 'Wildlife', 'Hot Springs', 'River', 'Forest',
                     'Beach', 'ADA']),
                ('obstacles',
                     ['Rocky', 'Over Grown', 'Bridge Out', 'No Shade', 'Old Growth', 'Washed Out', 'Closed', 'Scramble',
                     'Muddy', 'Blowdown', 'Private Property', 'Off Trail', 'Snow', 'Bugs'])
                ('routeType',
                     ['Loop', 'Out & Back', 'Point to Point'])
                ]:
            for c in fields:
                a = False
                b = False
                if c in t[f]:
                    magT = magT + 1
                    a = True
                if c in v[f]:
                    magV = magV + 1
                    b = True
                if a and b:
                    dot = dot + 1

        return dot / (sqrt(magT) * sqrt(magV))
    def score(vt, vr, tt, tr):
        # trail to trail similarity
        # TODO discuss weighting
        srev = score_rev(tr,vr)
        stra = score_trail(tt,vt)
        return (srev + stra) / 2.0
    return [(t, score(t,reviews[t['trail_id']],
                     trail,reviews[trail['trail_id']]))
           for t in valid if t['trail_id'] in reviews and trail['trail_id'] in reviews]


def make_ranking(valid, trail, keywords, reviews):
    """

    :return:
    """
    if trail is None and keywords is None:
        return valid
    elif trail is None:
        scored = calc_keyword_similarity(valid,keywords,reviews)
        return [t[0] for t in sorted(scored,key=lambda t: t[1],reverse=True)]
    elif keywords is None:
        scored = calc_trail_similarity(valid, trail, reviews)
        return [t[0] for t in sorted(scored,key=lambda t: t[1],reverse=True)]
    else:
        kwds = dict(calc_keyword_similarity(valid,keywords,reviews))
        trls = dict(calc_trail_similarity(valid, trail, reviews))
        scored = [(t, kwds[t] + trls[t]) for t in valid]
        return [t[0] for t in sorted(scored,key=lambda t: t[1],reverse=True)]

def filter_states(valid, state):
    """

    :return:
    """
    return [x for x in valid if state in x['states']]

def filter_distance(valid, query):
    """

    :return:
    """
    distance = float(query[0])
    location = query[1] #contains lat & lon
    lat = float(location[0])
    lon = float(location[1])
    return [x for x in valid if haversine(float(x['longitude']), float(x['latitude']), lon, lat) <= distance]


def filter_length(valid, length):
    """

    :return:
    """
    if length[0] is None:
        return [x for x in valid if float(x['length']) <= float(length[1])]
    elif length[1] is None:
        return [x for x in valid if float(x['length']) > float(length[0])]
    else:
        return [x for x in valid if float(length[1]) >= float(x['length']) > float(length[0])]

def filter_difficulty(valid, difficulty):
    """

    :return:
    """
    if difficulty[0] is None:
        return [x for x in valid if int(x['difficulty']) <= int(difficulty[1])]
    elif difficulty[1] is None:
        return [x for x in valid if int(x['difficulty']) > int(difficulty[0])]
    else:
        return [x for x in valid if int(difficulty[1]) >= int(x['difficulty']) > int(difficulty[0])]

def filter_start_altitude(valid, start_altitude):
    """

    :return:
    """
    if start_altitude[0] is None:
        return [x for x in valid if float(x['elevationStart']) <= float(start_altitude[1])]
    elif start_altitude[1] is None:
        return [x for x in valid if float(x['elevationStart']) > float(start_altitude[0])]
    else:
        return [x for x in valid if float(start_altitude[1]) >= float(x['elevationStart']) > float(start_altitude[0])]

def filter_max_altitude(valid, max_altitude):
    """

    :return:
    """
    if max_altitude[0] is None:
        return [x for x in valid if float(x['elevationMax']) <= float(max_altitude[1])]
    elif max_altitude[1] is None:
        return [x for x in valid if float(x['elevationMax']) > float(max_altitude[0])]
    else:
        return [x for x in valid if float(max_altitude[1]) >= float(x['elevationMax']) > float(max_altitude[0])]

def filter_change_altitude(valid, change_altitude):
    """

    :return:
    """
    if change_altitude[0] is None:
        return [x for x in valid if float(x['elevationGain']) <= float(change_altitude[1])]
    elif change_altitude[1] is None:
        return [x for x in valid if float(x['elevationGain']) > float(change_altitude[0])]
    else:
        return [x for x in valid if float(change_altitude[1]) >= float(x['elevationGain']) > float(change_altitude[0])]

def filter_tags(valid, tag):
    """

    :return:
    """
    return [x for x in valid if tag in x['features'] or x['activities'] or x['obstacles']]

def filter_routetypes(valid, routetypes):
    """

    :return:
    """
    return [x for x in valid if routetypes in x['rountType']]

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    # Radius of earth in miles is 6371
    miles = 3,959 * c
    return miles

if __name__ == "__main__":
	# trail = load_data()
  	# default = calc_default(trail)
  	# reviews = load_reviews()
  	print ("Flask app running at http://0.0.0.0:5000")
  	socketio.run(app, host="0.0.0.0", port=5000)

