import flask
from flask_login import login_required
from main import app, db, login_manager
from main.models import Player, Var
from main.module import Fetch, Skill, Reset, ParaUpdate, VarManager, isGameOver


# ログイン
@login_manager.user_loader
def load_user(user_id):
    return Player()

# トップビュー
@app.route('/')
def top_view():
    return flask.render_template('top.html')

# ログインの時に経由
@app.route('/login', methods=['GET','POST'])
def login():
    if flask.request.method == 'POST':
        # ユーザーチェック
        request_name = flask.request.form['user_name']
        request_password = flask.request.form['user_password']
        player = Player.query.filter_by(name=request_name, user_password=request_password).all()
        # もし存在したら
        if len(player) > 0:
            user_id = player[0].user_id
            group_id = player[0].group_id
            return flask.redirect(flask.url_for('wait_view', group_id=group_id, user_id=user_id))
        else:
            return flask.redirect(flask.url_for('top_view'))
    else:
        return None

# ユーザー登録
@app.route('/create')
def create_view():
    return flask.render_template('create.html')

# 待機部屋
@app.route('/wait/<int:group_id>/<int:user_id>')
def wait_view(group_id, user_id):
    return ParaUpdate.gather_completed(group_id, user_id)

# 準備オッケーボタンを押すとここに一瞬飛ぶ
@app.route('/prepare', methods=['POST'])
def prepareration_okay():
    group_id = int(flask.request.form['group_id'])
    user_id = int(flask.request.form['user_id'])
    # メンバーが集まったと判断した人はis_got_togetherを更新
    ParaUpdate.all_member_gathered(user_id)
    return ParaUpdate.gather_completed(group_id, user_id)


# スタート
@app.route('/start/<int:group_id>/<int:user_id>')
def start_view(group_id, user_id):
    # グローバル変数を作る
    VarManager.set_global_var(group_id)
    login_user = Player.query.get(user_id)
    return flask.render_template('start.html', group_id=group_id, login_user=login_user)


# 夜の画面
@app.route('/night/<int:group_id>/<int:user_id>')
def night_view(group_id, user_id):
    login_user = Player.query.get(user_id)
    players = Fetch.alive_players(group_id)
    if login_user.role == "人狼":
        pass
    return flask.render_template('night.html', group_id=group_id, login_user=login_user, players=players)


# 夜の行動の後一瞬いくURL
@app.route('/night_action', methods=['POST'])
def night_action():
    # formから受け取る
    group_id = int(flask.request.form['group_id'])
    user_id = int(flask.request.form['user_id'])
    login_user = Player.query.get(user_id)
    if login_user.role == "人狼":
        bitten_id = int(flask.request.form['bite'])
        ParaUpdate.bite_done(user_id, bitten_id)
    return flask.redirect(flask.url_for('morning_view', group_id=group_id, user_id=user_id))


# 朝の画面
@app.route('/morning/<int:group_id>/<int:user_id>')
def morning_view(group_id, user_id):
    return ParaUpdate.bite_completed(group_id, user_id)

# morningの後に一瞬ここに飛ぶ
@app.route('/noon/<int:group_id>/<int:user_id>')
def noon(group_id, user_id):
    # ここでパラメータを整理する
    Reset.para_refresh(group_id)  # パラメーターリフレッシュ
    if VarManager.fetch_value(group_id, 'killed_player_id'):  # 昨晩襲撃されていれば
        ParaUpdate.die(VarManager.fetch_value(group_id, 'killed_player_id'))
    # 終了条件
    if isGameOver.is_village_win(group_id) != 2:
        return flask.redirect(flask.url_for('end_view', group_id=group_id, user_id=user_id))
    else:
        return flask.redirect(flask.url_for('day_view', group_id=group_id, user_id=user_id))

# 昼の画面
@app.route('/day/<int:group_id>/<int:user_id>')
def day_view(group_id, user_id):
    # その後にオブジェクト取ってくる
    login_user = Player.query.get(user_id)
    players = Fetch.alive_players(group_id)
    dead_players = Fetch.dead_players(group_id)
    return flask.render_template('day.html', group_id=group_id, login_user=login_user, players=players, dead_players=dead_players)

# 投票フォーム
@app.route('/vote_form/<int:group_id>/<int:user_id>')
def vote_form(group_id, user_id):
    login_user = Player.query.get(user_id)
    players = Fetch.alive_players(group_id)
    return flask.render_template('vote_form.html', group_id=group_id, login_user=login_user, players=players)

# 投票時に一瞬いくURL
@app.route('/vote', methods=['POST'])
def vote():
    # formから受け取る
    group_id = int(flask.request.form['group_id'])
    user_id = int(flask.request.form['user_id'])
    voted_id = int(flask.request.form['vote'])
    # 投票してパラメータを更新
    ParaUpdate.vote_done(user_id, voted_id)  #　自作メソッド
    return flask.redirect(flask.url_for('vote_result', group_id=group_id, user_id=user_id))

# 投票結果画面
@app.route('/vote_result/<int:group_id>/<int:user_id>')
def vote_result(group_id, user_id):
    return ParaUpdate.vote_completed(group_id, user_id)

# 投票した後一瞬いくURL
@app.route('/evening/<int:group_id>/<int:user_id>')
def evening(group_id, user_id):
    # 処刑
    ParaUpdate.die(VarManager.fetch_value(group_id, 'executed_player_id'))
    # 終了条件
    if isGameOver.is_village_win(group_id) != 2:
        return flask.redirect(flask.url_for('end_view', group_id=group_id, user_id=user_id))
    else:
        return flask.redirect(flask.url_for('night_view', group_id=group_id, user_id=user_id))

# ゲームオーバー画面
@app.route('/end/<int:group_id>/<int:user_id>')
def end_view(group_id, user_id):
    return flask.render_template('end.html')


# プレイヤー追加
@app.route('/add', methods=['POST'])
def add_player():
    player = Player(
        name=flask.request.form['user_name'],
        is_alive=True,
        role="村人",
        user_password=flask.request.form['user_password'],
        group_id=flask.request.form['group_id'],
        group_password=flask.request.form['group_password'],
    )
    db.session.add(player)
    db.session.commit()
    return flask.redirect(flask.url_for('top_view'))

