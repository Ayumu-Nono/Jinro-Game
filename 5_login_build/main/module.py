import flask
from flask_login import login_required
from main import app, db, login_manager
from main.models import Player, Var
import random

"""便利モジュール"""


class VarManager:
    
    """
        Var（変数モデル）を管理する
    """

    # ゲームの最初に変数を作る。まとめて作る
    def set_global_var(group_id) -> None:
        VarManager.create_var(group_id, 'killed_player_id')
        VarManager.create_var(group_id, 'executed_player_id')

    # 変数名入れたらあとはやってくれる
    def create_var(group_id, name: str) -> None:
        var = Var(
            group_id=group_id,
            name=name,
            value=0,
        )
        db.session.add(var)
        db.session.commit()
    
    # 変数名と代入したい値を渡すと保存くれる
    def save_value(group_id: int, name: str, value: int) -> int:
        var = Var.query.filter(Var.group_id == group_id, Var.name == name).all()
        var = var[0]
        var.value = value
        db.session.add(var)
        db.session.commit()

    # 変数名から値を取ってきてくれる
    def fetch_value(group_id: int, name: str) -> int:
        var = Var.query.filter(Var.group_id == group_id, Var.name == name).all()
        if len(var) > 1:
            for i in range(1, len(var)):
                db.session.delete(var[i])
        var = var[0]
        return var.value




class Fetch:

    """
        オブジェクト取ってくる系
        Player（プレイヤーモデル）
    """
    # グループ内の全員をとってくる
    def all_players(group_id):
        players = Player.query.filter(Player.group_id == group_id).all()
        return players

    # グループ内の生きている人をとってくる
    def alive_players(group_id):
        players = Player.query.filter(Player.group_id == group_id, Player.is_alive == True).all()
        return players

    # グループ内の死んでいる人をとってくる
    def dead_players(group_id):
        players = Player.query.filter(Player.group_id == group_id, Player.is_alive == False).all()
        return players
    
    # 生きてる村人のプレイヤーを取ってくる
    def alive_villager(group_id):
        players = Player.query.filter(Player.group_id == group_id, Player.role == "村人").all()
        return players

    # 生きてる人狼のプレイヤーを取ってくる
    def alive_werewolf_players(group_id):
        players = Player.query.filter(Player.group_id == group_id, Player.role == "人狼").all()
        return players

    # 生きてる狂人のプレイヤーを取ってくる
    def alive_madman_players(group_id):
        players = Player.query.filter(Player.group_id == group_id, Player.role == "狂人").all()
        return players



class Skill:

    """能力系"""

    # 人狼の能力：噛み殺す
    def bite(player_id):
        bitten_player = Player.query.get(player_id)
        bitten_player.bitten += 1
        db.session.add(bitten_player)
        db.session.commit()
        return None

    # 占い師の能力：占う
    def forecast(player_id) -> bool:
        forecasted_player = Player.query.get(player_id)
        role = forecasted_player.role
        if role == '人狼':
            is_werewolf = True
        else:
            is_werewolf = False
        return is_werewolf

    # 霊媒師の能力：死者を見る
    def confirm(player_id) -> bool:
        confirmed_player = Player.query.get(player_id)
        role = confirmed_player.role
        if role == '人狼':
            is_werewolf = True
        else:
            is_werewolf = False
        return is_werewolf

    # 狩人の能力：守る
    def protect(player_id) -> None:
        protected_player = Player.query.get(player_id)
        protected_player.is_protected = True
        db.session.add(protected_player)
        db.session.commit()
        return None


class Reset:

    """リセット系"""

    # 各種パラメータのリセット（グループ内の生きてる人全員）
    def para_refresh(group_id) -> None:
        players = Fetch.alive_players(group_id)
        for i in range(len(players)):
            player = players[i]    
            # 受動系パラメータ
            player.votes = 0
            player.is_protected = False
            player.bitten = 0
            # 権利系パラメータ
            player.can_vote = True
            if player.role == "村人":
                pass
            elif player.role == "占い師":
                player.can_forecast = True
            elif player.role == "霊媒師":
                player.can_confirm = True
            elif player.role == "狩人":
                player.can_protect = True
            elif player.role == "人狼":
                player.can_bite = True
            elif player.role == "狂人":
                pass
            else:
                return "エラー"
            # データベース更新
            db.session.add(player)
            db.session.commit()

    # ゲーム開始時のオールリセット（全員村人になる）
    def gamestart_refresh(group_id) -> None:
        players = Fetch.all_players(group_id)
        for i in range(len(players)):
            player = players[i]
            # メタパラメータリセット
            player.is_alive = True
            player.role = "村人"
            player.votes = 0
            player.is_protected = False
            player.bitten = 0
            # 権利系パラメータ
            player.can_vote = True
            player.can_bite = False
            player.can_protect = False
            player.can_forecast = False
            player.can_confirm = False
            # グループ管理系
            player.is_got_together = True
            # データベース更新
            db.session.add(player)
            db.session.commit()
    
    # ゲーム開始時の役職振り分け
    def set_roles(group_id) -> None:
        # 村人から取ってくる
        players = Fetch.alive_villager(group_id)
        # ひとり人狼
        print(players)
        werewolf = random.sample(players, 1)[0]
        werewolf.role = "人狼"
        db.session.add(werewolf)
        db.session.commit()
            





class ParaUpdate:

    """
    パラメータ更新系
        0.誰かが死んだ時更新 
        1.権利系更新
        2.最終的なパラメーター更新（処刑、襲撃など）
        3.ゲーム開始時
    """

    """0.誰がが死んだ時データベースを更新"""
    def die(user_id) -> None:
        player = Player.query.get(user_id)
        player.is_alive = False
        db.session.add(player)
        db.session.commit()

    """
    1.権利系パラメータ更新
        Skillクラスと組み合わせて使う
    """

    # 投票が実行時に実行する
    def vote_done(user_id, voted_id) -> None:
        # 投票が完了したプレイヤーの投票券を更新
        vote_player = Player.query.get(user_id)
        vote_player.can_vote = False
        db.session.add(vote_player)
        # 投票されたプレイヤーの得票数を更新
        voted_player = Player.query.get(voted_id)
        voted_player.votes += 1
        db.session.add(voted_player)
        # データベース更新
        db.session.commit()
        
    # 人狼の能力発揮時に実行
    def bite_done(user_id, bitten_id) -> None:
        # 噛みが完了したプレイヤーの噛む券を更新
        bite_player = Player.query.get(user_id)
        bite_player.can_bite = False
        db.session.add(bite_player)
        db.session.commit()
        # 噛まれたプレイヤーの噛まれ数を更新
        Skill.bite(bitten_id)

    # 占い能力発揮時に実行
    def forecast_done(user_id, forecasted_id) -> bool:
        # 占いが完了したプレイヤーの占い券を更新
        forecast_player = Player.query.get(user_id)
        forecast_player.can_forecast = False
        db.session.add(forecast_player)
        db.session.commit()
        # 占い結果を返す
        return Skill.forecast(forecasted_id)

    # 霊媒能力発揮時に実行
    def confirm_done(user_id, confirmed_id) -> bool:
        # 霊媒が完了したプレイヤーの霊媒券を更新
        confirm_player = Player.query.get(user_id)
        confirm_player.can_confirm = False
        db.session.add(confirm_player)
        db.session.commit()
        # 霊媒結果を返す
        return Skill.confirm(confirmed_id)

    # 狩人の能力発揮時に実行
    def protect_done(user_id, protected_id) -> None:
        # 守護が完了したプレイヤーの守護券を更新
        protect_player = Player.query.get(user_id)
        protect_player.can_protect = False
        db.session.add(protect_player)
        db.session.commit()
        # 守護されたプレイヤーの守護パラメータを更新
        Skill.protect(protected_id)

    """"2.最終的なパラメーター更新（処刑、襲撃など）"""

    # 投票終了判定 & 処刑される人を決定メソッド
    # ついでにrender返しとく
    def vote_completed(group_id, user_id):
        login_user = Player.query.get(user_id)
        is_vote_completed = False
        players = Fetch.alive_players(group_id)
        votes_sum = 0  # 投票総数
        executed_player = None
        for i in range(len(players)):
            votes_sum += players[i].votes
        if votes_sum >= len(players):  # 全員が投票すれば
            is_vote_completed = True
            executed_player = Player.query.order_by(-Player.votes)[0]  # 処刑される人
            VarManager.save_value(group_id, 'executed_player_id', executed_player.user_id)  # 処刑される人のidを保存
            return flask.render_template('vote_result.html', group_id=group_id, login_user=login_user, is_vote_completed=is_vote_completed, executed_player=executed_player)    
        else:  # 投票が終わってない時
            return flask.render_template('vote_result.html', group_id=group_id, login_user=login_user, is_vote_completed=is_vote_completed, executed_player=executed_player)    

    # 襲撃終了判定 & 襲撃される人を決定メソッド
    # ついでにrender返しとく
    def bite_completed(group_id, user_id):
        login_user = Player.query.get(user_id)
        is_bite_completed = False
        players = Fetch.alive_players(group_id)
        bitten_sum = 0  # 噛み総数
        killed_player = None
        for i in range(len(players)):
            bitten_sum += players[i].bitten
        if bitten_sum >= len(Fetch.alive_werewolf_players(group_id)):  # 人狼全員が投票すれば
            is_bite_completed = True
            killed_player = Player.query.order_by(-Player.bitten)[0]  # 処刑される人
            if killed_player.is_protected:  # 守られていれば
                killed_player = None
            else:  # 守られていなければ
                pass
            VarManager.save_value(group_id, 'killed_player_id', killed_player.user_id)  # 噛まれる人のidを保存
            return flask.render_template('morning.html', group_id=group_id, login_user=login_user, is_bite_completed=is_bite_completed, killed_player=killed_player)
        else:  # 人狼がまだ投票し終わってない時
            return flask.render_template('morning.html', group_id=group_id, login_user=login_user, is_bite_completed=is_bite_completed, killed_player=killed_player)

    """3.ゲーム開始時"""

    # メンバーが集まったと判断した人はis_got_togetherを更新
    def all_member_gathered(user_id):
        user = Player.query.get(user_id)
        user.is_got_together = True
        db.session.add(user)
        db.session.commit()

    # メンバーが全員集まったと全員が判定したらゲームスタート
    # ついでにrender返しとく
    def gather_completed(group_id, user_id):
        login_user = Player.query.get(user_id)
        is_preparation_okay = login_user.is_got_together
        players = Fetch.all_players(group_id)
        gather_sum = 0  # 準備オッケー総数
        
        for i in range(len(players)):
            if players[i].is_got_together:
                gather_sum += 1
        if gather_sum >= len(players):  # メンバー全員が準備オッケーになれば
            # 全員準備オッケになれば役職振り分けしたい
            Reset.gamestart_refresh(group_id)  # 全員村人
            Reset.set_roles(group_id)  # そこから役職振り分け
            return flask.redirect(flask.url_for('start_view', group_id=group_id, user_id=user_id))
        else:  # まだ準備が終わってない人がいれば
            return flask.render_template('wait.html', group_id=group_id, login_user=login_user, is_preparation_okay=is_preparation_okay, players=players)


class isGameOver:

    """
        ゲームオーバー判定
    """

    # 判定。
    # 村側目線で勝利なら1を返す。
    # 負けたら0
    # 続くなら2を返す
    def is_village_win(group_id) -> bool:
        all_alive = Fetch.alive_players(group_id)
        werewolfs = Fetch.alive_werewolf_players(group_id)
        madman = Fetch.alive_madman_players(group_id)
        # 白と黒の人数
        num_werewolfs = len(werewolfs)
        num_black = len(madman) + num_werewolfs
        num_white = len(all_alive) - num_black
        # 判定
        is_village_win = 2
        if num_werewolfs == 0:
            is_village_win = 1
        elif num_black >= num_white:
            is_village_win = 0
        else:
            pass
        return is_village_win
    