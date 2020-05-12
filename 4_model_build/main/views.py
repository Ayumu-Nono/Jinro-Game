import flask
from main import app, db
from main.models import Player
import time

# プレイヤー一覧
@app.route('/')
def show_players():
    players = Player.query.all()
    return flask.render_template('players.html', players=players)

# 昼の画面
@app.route('/day')
def day():
    players = Player.query.filter(Player.is_alive)
    dead_players = Player.query.filter(not Player.is_alive)
    return flask.render_template('day.html', players=players, dead_players=dead_players)

# 投票フォーム
@app.route('/vote_form')
def vote_form():
    players = Player.query.all()
    return flask.render_template('vote_form.html', players=players)


# 投票結果画面
@app.route('/vote_result')
def vote_result():
    vote_completed = False
    players = Player.query.all()
    votes_sum = 0  # 投票総数
    for i in range(len(players)):
        votes_sum += players[i].votes
    if votes_sum >= len(players):  # 全員が投票すれば
        vote_completed = True
        executed_player = Player.query.order_by(-Player.votes)[0]  # 処刑される人
    return flask.render_template('vote_result.html', vote_completed=vote_completed, players=players, executed_player=executed_player)


# 投票時に一瞬いくURL
@app.route('/vote', methods=['POST'])
def vote():
    pk = flask.request.form['vote']
    pk = int(pk)
    voted_player = Player.query.filter_by(id=pk).all()[0]
    voted_player.votes += 1
    db.session.add(voted_player)
    db.session.commit()
    return flask.redirect(flask.url_for('vote_result'))

# 夜の画面
@app.route('/night')
def night():
    return flask.render_template('night.html')

# プライヤー追加
@app.route('/add', methods=['POST'])
def add_player():
    player = Player(
        name=flask.request.form['name'],
        # is_alive=flask.request.form['is_alive'],
        is_alive=True,
        role=flask.request.form['role'],
    )
    db.session.add(player)
    db.session.commit()
    return flask.redirect(flask.url_for('show_players'))
