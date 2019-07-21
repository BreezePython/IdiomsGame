import sqlite3
from flask import Flask, render_template, request, g, session, redirect, url_for, jsonify
import random
from pypinyin import pinyin

app = Flask(__name__)
DATABASE = 'static/db/database.db'
app.secret_key = 'Breeze Python'


def connect_db():
    return sqlite3.connect(DATABASE)


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def query_db(query, args=(), one=True):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    if not query.startswith('select'):
        g.db.commit()
    return (rv[0] if rv else None) if one else rv


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user = request.form.get('name')
        session['user'] = user
        session['round'] = 1
        return redirect(url_for('game'))
    rank_list = query_db('select * from rank order by round_num desc limit 5',one=False)
    print(rank_list)
    return render_template('login.html', rank_list=rank_list)


@app.route('/game')
def game():
    if not session.get('user'):
        return redirect(url_for('index'))
    id = random.randint(1, 30000)
    idiom = query_db('select * from idiom where id = ?',
                     [id])
    return render_template('game.html', user=session.get('user'), idiom=idiom)


@app.route('/more/<user_idiom>')
def more(user_idiom):
    speak_list = pinyin(user_idiom)
    print(speak_list[0][-1])
    idiom_speak = '  '.join(map(lambda x: x[0], speak_list))
    if query_db('select * from idiom where speak = ?',
                [idiom_speak]):
        new_idiom = query_db("select * from idiom where speak like ('%s%%')" % speak_list[-1][0])
        session['round'] = session.get('round') + 1
        print({'code': 200, 'round': session.get('round'), 'info': new_idiom})
        return jsonify({'code': 200, 'round': session.get('round'), 'info': new_idiom})
    else:
        query_db('replace into rank (name,round_num) values (?,?)',
                 [session.get('user'), session.get('round')])
        return jsonify({'code': 404, 'error': "挑战结束：用户输入的成语是自己编的吧！", 'url': request.host_url})
