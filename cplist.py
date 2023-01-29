# curl -i -H "Content-Type: application/json" -X POST -d '{"torpath" : "~/torccf/frds_10018_tt6710716/真探S03.2019.1080p.WEB-DL.x265.AC3￡cXcY@FRDS", "torhash": "289256b0918c3dccea51a194a3e834664b17eafd", "torsize": "11534336"}' http://localhost:5000/api/torcp

from flask import Flask, render_template, jsonify
from flask import request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sys
import os
from torcp.torcp import Torcp
import logging
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

#### TODO: Change this!
users = {
    "abcde": generate_password_hash("Href119"),
    "root": generate_password_hash("aJax110")
}


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
auth = HTTPBasicAuth()

def genSiteLink(siteAbbrev, siteid, sitecat=''):
    SITE_URL_PREFIX = {
        'pter': 'https://pterclub.com/details.php?id=',
        'pterclub': 'https://pterclub.com/details.php?id=',
        'aud': 'https://audiences.me/details.php?id=',
        'audiences': 'https://audiences.me/details.php?id=',
        'chd': 'https://chdbits.co/details.php?id=',
        'chdbits': 'https://chdbits.co/details.php?id=',
        'lhd': 'https://lemonhd.org/',
        'hds': 'https://hdsky.me/details.php?id=',
        'hdsky': 'https://hdsky.me/details.php?id=',
        'ob': 'https://ourbits.club/details.php?id=',
        'ssd': 'https://springsunday.net/details.php?id=',
        'frds': 'https://pt.keepfrds.com/details.php?id=',
        'hh': 'https://hhanclub.top/details.php?id=',
        'ttg': 'https://totheglory.im/t/',
        }
    detailUrl = ''
    if siteAbbrev in SITE_URL_PREFIX:
        if siteAbbrev == 'lhd':
            if sitecat == 'movie':
                detailUrl = SITE_URL_PREFIX[siteAbbrev] + 'details_movie.php?id=' + str(siteid)
            elif sitecat == 'tvseries':
                detailUrl = SITE_URL_PREFIX[siteAbbrev] + 'details_tv.php?id=' + str(siteid)
        else:
            detailUrl = SITE_URL_PREFIX[siteAbbrev] + str(siteid)
    return detailUrl if detailUrl else '#'


class TorMediaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    addedon = db.Column(db.DateTime, default=datetime.now)
    torname = db.Column(db.String(256), index=True)
    torsite = db.Column(db.String(64))
    torsiteid = db.Column(db.Integer)
    torsitecat = db.Column(db.String(20))
    torimdb = db.Column(db.String(20), index=True)
    torhash = db.Column(db.String(120))
    torsize = db.Column(db.Integer)
    tmdbid = db.Column(db.String(120))
    tmdbcat = db.Column(db.String(20))
    location = db.Column(db.String(256))
    plexid = db.Column(db.String(120))

    def to_dict(self):
        return {
            'torname': self.torname,
            'addedon': self.addedon,
            'torabbrev': self.torsite,
            'torsite': genSiteLink(self.torsite,self.torsiteid),
            'torsitecat': self.torsitecat,
            'torimdb': self.torimdb,
            'tmdbid': str(self.tmdbid),
            'tmdbcat': self.tmdbcat,
            'location': self.location,
        }


with app.app_context():
    db.create_all()


class TorcpItemDBObj:
    def __init__(self, torsite, torsiteid, torimdb, torhash, torsize):
        self.torsite = torsite
        self.torsiteid = torsiteid
        self.torimdb = torimdb
        self.torhash = torhash
        self.torsize = torsize

    def onOneItemTorcped(self, targetDir, mediaName, tmdbIdStr, tmdbCat):
        # print(targetDir, mediaName, tmdbIdStr, tmdbCat)
        t = TorMediaItem(torname=mediaName,
                    torsite=self.torsite,
                    torsiteid=self.torsiteid,
                    torimdb=self.torimdb,
                    torhash=self.torhash,
                    torsize=self.torsize,
                    tmdbid=tmdbIdStr,
                    tmdbcat=tmdbCat,
                    location=targetDir)
        with app.app_context():
            db.session.add(t)
            db.session.commit()


def queryByHash(qbhash):
    with app.app_context():
        query = db.session.query(TorMediaItem).filter(TorMediaItem.torhash == qbhash).first()
        return query


@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


@app.route('/')
@auth.login_required
def index():
    return render_template('ajax_table.html', title='Ajax Table')

@app.route('/url/detail')
def siteDetail(siteAbbrev, siteid):

    return 

@app.route('/editconf', methods=['POST', 'GET'])
@auth.login_required
def editconf():
    # fn = 'config.ini'
    # with open(fn, 'r') as f:
    #     config_ini = f.read()
    # if request.method == 'POST':
    #     config_ini = request.form['text_box']
    #     with open(fn, 'w') as f:
    #         f.write(str(config_ini))
    config_ini = 'under construction....'
    return render_template('edit_config.html', config_file=config_ini)


@app.route('/api/data')
@auth.login_required
def data():
    query = TorMediaItem.query

    # search filter
    search = request.args.get('search[value]')
    if search:
        query = query.filter(db.or_(
            TorMediaItem.torname.like(f'%{search}%'),
            TorMediaItem.location.like(f'%{search}%')
        ))
    total_filtered = query.count()

    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f'order[{i}][column]')
        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        if col_name not in ['torname', 'torsite', 'addedon', 'torsize']:
            col_name = 'name'
        descending = request.args.get(f'order[{i}][dir]') == 'desc'
        col = getattr(TorMediaItem, col_name)
        if descending:
            col = col.desc()
        order.append(col)
        i += 1
    if order:
        query = query.order_by(*order)

    # pagination
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    query = query.offset(start).limit(length)

    # response
    return {
        'data': [user.to_dict() for user in query],
        'recordsFiltered': total_filtered,
        'recordsTotal': TorMediaItem.query.count(),
        'draw': request.args.get('draw', type=int),
    }



@app.route('/api/torcp', methods=['POST'])
@auth.login_required
def runTorcp():
    if 'torpath' in request.json and 'torhash' in request.json and 'torsize' in request.json:
        npath = os.path.normpath(request.json['torpath'].strip())
        torname = os.path.basename(npath)
        site_id_imdb = os.path.basename(os.path.dirname(npath))
        site = ''
        siteid = ''
        torimdb = ''
        if "_" in site_id_imdb:
            l = site_id_imdb.split("_")
            if len(l) == 3:
                site, siteid, torimdb = l[0], l[1], l[2]
            elif len(l) == 2:
                site, siteid = l[0], l[1]

        argv = [npath, "-d", "~/torccf/result", "-s", "--lang", "cn,ja,ko", "--tmdb-api-key",
                "9e0791be4a66b90b471e6d3c4674e084", "--make-log", "--emby-bracket", "--extract-bdmv", "--tmdb-origin-name"]
        eo = TorcpItemDBObj(site, siteid, torimdb, 
                            request.json['torhash'].strip(), 
                            request.json['torsize'].strip())
        o = Torcp()
        o.main(argv, eo)
        return jsonify({'OK': 200}), 200
    return jsonify({'Error': 401}), 401


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True)
