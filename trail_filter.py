import os, csv, math, re
import pprint
from math import radians, cos, sin, asin, sqrt

def load_data():
    """

    :return:
    """
    trail = {}
    reader = csv.DictReader(open('sample_trail.csv', 'rb'))
    for line in reader:
        trail[line['trailId']] = line
    return trail


def clean(string):
    return re.compile("\w+").findall(string.lower())


def load_reviews():
    reviews = {'all': set([])}
    reader = csv.DictReader(open('sample_reviews.csv', 'rb'))
    for line in reader:
        if '' == line['comment']:
            continue
        tid = line['trailId']
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
    tmp = [(t, score(reviews[t['trailId']],keywords)) for t in valid]
    m = max(tmp, key=lambda l: l[1])
    return [(a,b/m) for (a,b) in tmp]


def calc_trail_similarity(valid, trail, reviews):
    def score_rev(twords, kwords):
        dot = sum([kwords[0][w]*twords[0][w] for w in kwords[0] if w in twords[0]]) / twords[1] / kwords[1]
        tmag = math.sqrt(sum([twords[0][w]*twords[0][w] for w in twords[0]]))
        kmag = math.sqrt(sum([kwords[0][w]*kwords[0][w] for w in kwords[0]]))
        return dot / (tmag * kmag)
    def score_trail(t, v):
        #TODO calculate trail feature similarity
        return 0
        pass
    def score(vt, vr, tt, tr):
        # trail to trail similarity
        # TODO discuss weighting
        srev = score_rev(tr,vr)
        stra = score_trail(tt,vt)
        return (srev + stra) / 2.0
    return [(t, score(t,reviews[t['trailId']],
                     trail,reviews[trail['trailId']]))
           for t in valid if t['trailId'] in reviews and trail['trailId'] in reviews]


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

if __name__ == '__main__':
    trail = load_data()
    default = calc_default(trail)
    reviews = load_reviews()
    query = {}
    query['trail'] = trail['10029098']
    query['keywords'] = None
    result = handle_query(query, default,reviews)
    #print(len(result))
    #pprint.pprint(result)
    rev = load_reviews()
    pprint.pprint(rev)