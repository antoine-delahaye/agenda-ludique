# app/site/views.py

import flask_login
from flask import render_template, redirect, url_for, request, make_response
from flask_login import login_required, current_user
from sqlalchemy import text

from app import db
from app.models import User, Game, Group, HideUser, BookmarkUser, Collect, Wish, HideGame
from app.site import site
from app.site.forms import UpdateInformationForm, GamesSearchForm, UsersSearchForm


@site.route('/')
def home():
    """
    Render the homepage template on the / route
    """
    return render_template('home.html', stylesheet='home')


# Games adding/editing related ###################################################
@site.route('/catalog')
@login_required
def catalog():
    """
    Render the catalog template on the /catalog route
    """
    page = request.args.get('page', 1, type=int)
    games = Game.query.paginate(page=page, per_page=20)
    owned_games = User.get_owned_games(flask_login.current_user.id, True)
    wished_games = User.get_wished_games(flask_login.current_user.id, True)
    return render_template('catalog.html', stylesheet='catalog', games=games, owned_games=owned_games,
                           wished_games=wished_games)


@site.route('/library')
@login_required
def library():
    """
    Render the library template on the /library route
    """
    page = request.args.get('page', 1, type=int)
    owned_games = User.get_owned_games(flask_login.current_user.id).paginate(page=page, per_page=20)
    wished_games = User.get_wished_games(flask_login.current_user.id, True)
    return render_template('library.html', stylesheet='library', owned_games=owned_games, wished_games=wished_games)


@site.route('/add-collection', methods=['GET', 'POST'])
@site.route('/add-collection/<game_id>', methods=['GET', 'POST'])
@login_required
def add_game_collection(game_id):
    db.session.add(Collect(user_id=flask_login.current_user.id, game_id=game_id))
    db.session.commit()
    return redirect(request.referrer)


@site.route('/remove', methods=['GET', 'POST'])
@site.route('/remove/<game_id>', methods=['GET', 'POST'])
@login_required
def remove_game_collection(game_id):
    db.session.delete(Collect.query.filter_by(user_id=flask_login.current_user.id, game_id=game_id).first())
    db.session.commit()
    return redirect(request.referrer)


@site.route('/wishes')
@login_required
def wishes():
    """
    Render the library template on the /wish route
    """
    page = request.args.get('page', 1, type=int)
    wished_games = User.get_wished_games(flask_login.current_user.id).paginate(page=page, per_page=20)
    owned_games = User.get_owned_games(flask_login.current_user.id, True)
    return render_template('wishes.html', stylesheet='library', wished_games=wished_games, owned_games=owned_games)


@site.route('/add-wishes', methods=['GET', 'POST'])
@site.route('/add-wishes/<game_id>', methods=['GET', 'POST'])
@login_required
def add_game_wish(game_id):
    db.session.add(Wish(user_id=flask_login.current_user.id, game_id=game_id))
    db.session.commit()
    return redirect(request.referrer)


@site.route('/remove-wishes', methods=['GET', 'POST'])
@site.route('/remove-wishes/<game_id>', methods=['GET', 'POST'])
@login_required
def remove_game_wish(game_id):
    db.session.delete(Wish.query.filter_by(user_id=flask_login.current_user.id, game_id=game_id).first())
    db.session.commit()
    return redirect(request.referrer)


# Account/Profil related #########################################################
@site.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    """
    Render the users template on the /users route
    """
    form = UsersSearchForm()
    page = request.args.get('page', 1, type=int)
    username_hint = request.args.get('username', '', type=str)
    search_parameters = []
    qs_search_parameters = request.args.get('searchParameters', None, type=str)

    if form.validate_on_submit():
        username_hint = form.username_hint.data

        if form.display_masked_players.data:
            search_parameters.append("HIDDEN")

        if form.display_favorites_players_only.data:
            search_parameters.append("ONLY_BOOKMARKED")

    if qs_search_parameters:
        # Add the search parameters contained in the query string into the search_parameters list
        parameters_list = qs_search_parameters.split(',')
        for parameter in parameters_list:
            search_parameters.append(parameter)
            # Show in the advanced search menu the enabled parameters
            if parameter == "ONLY_BOOKMARKED":
                form.display_favorites_players_only.data = True
            if parameter == "HIDDEN":
                form.display_masked_players.data = True

    search_results = User.search_with_pagination(current_user, username_hint, search_parameters, page, 20)

    return render_template('users.html', stylesheet='users', form=form, current_user_id=current_user.id, users_data=search_results)


@site.route('/user')
@site.route('/user/<int:id>', methods=['GET', 'POST'])
@login_required
def user(id=None):
    """
    Render the user template on the /user route
    """
    user = User.query.get_or_404(id)
    return render_template('user.html', stylesheet='user', user=user)


@site.route('/hidden-users/add', methods=['GET'])
@login_required
def add_hidden_user(user_id=None):
    """
    Add the declared user (property "user" in the query string) to the hidden users
    on the /hidden-users/add route.
    """
    connected_user = current_user
    user_id = request.args.get('user')

    if user_id is not None:
        user_to_hide = User.query.get(user_id)
        if user_to_hide is not None:
            hidden_user = HideUser(user_id=connected_user.id, user2_id=user_to_hide.id)
            db.session.add(hidden_user)
            db.session.commit()

    return redirect(url_for('site.users'))


@site.route('/hidden-users/remove', methods=['GET'])
@login_required
def remove_hidden_user(user_id=None):
    """
    Remove the declared user (property "user" in the query string) from the hidden users
    on the /hidden-users/remove route.
    """
    connected_user = current_user
    user_id = request.args.get('user')

    if user_id is not None:
        user_to_remove = User.query.get(user_id)
        if user_to_remove is not None:
            hidden_user = HideUser.query.get({"user_id": connected_user.id, "user2_id": user_to_remove.id})
            if hidden_user is not None:
                db.session.delete(hidden_user)
                db.session.commit()

    return redirect(url_for('site.users', searchParameters="HIDDEN"))


@site.route('/bookmarked-users/add', methods=['GET'])
@login_required
def add_bookmarked_user(user_id=None):
    """
    Add the declared user (property "user" in the query string) to the bookmarked users
    on the /bookmarked-users/add route.
    """
    connected_user = current_user
    user_id = request.args.get('user')

    if user_id is not None:
        user_to_bookmark = User.query.get(user_id)
        if user_to_bookmark is not None:
            bookmarked_user = BookmarkUser(user_id=connected_user.id, user2_id=user_to_bookmark.id)
            db.session.add(bookmarked_user)
            db.session.commit()

    return redirect(url_for('site.users'))


@site.route('/bookmarked-users/remove', methods=['GET'])
@login_required
def remove_bookmarked_user(user_id=None):
    """
    Remove the declared user (property "user" in the query string) from the bookmarked users
    on the /bookmarked-users/remove route.
    """
    connected_user = current_user
    user_id = request.args.get('user')

    if user_id is not None:
        user_to_remove = User.query.get(user_id)
        if user_to_remove is not None:
            bookmarked_user = BookmarkUser.query.get({"user_id": connected_user.id, "user2_id": user_to_remove.id})
            if bookmarked_user is not None:
                db.session.delete(bookmarked_user)
                db.session.commit()

    return redirect(url_for('site.users'))


@site.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    """
    Render the account template on the /account route
    """
    form = UpdateInformationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=flask_login.current_user.email).first()
        if user is not None:
            user.username = form.username.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.password = form.password.data
            user.profile_picture = form.profile_picture.data
            db.session.commit()
        return redirect(url_for('site.account'))
    return render_template('account.html', stylesheet='account', form=form)


@site.route('/parameters')
@login_required
def parameters():
    """
    Render the parameters template on the /parameters route
    """
    return render_template('parameters.html', stylesheet=None)


@site.route('/set_parameters', methods=['POST'])
@login_required
def set_parameters():
    color_theme = "On" if request.form.get('color-theme') is not None else "Off"
    param = make_response(redirect(url_for('site.parameters')))
    param.set_cookie('color-theme', color_theme)
    return param


# Group related ##################################################################
@site.route('/groups')
@login_required
def groups():
    """
    Render the groups template on the /groups route
    """
    groups_data = []
    for data in db.session.query(Group).all():
        groups_data.append(
            {'id': int(data.id), 'name': data.name})
    return render_template('groups.html', stylesheet='groups', groups_data=groups_data)


@site.route('/groups_private')
@login_required
def groups_private():
    """
    Render the groups template on the /groups_private route
    """
    groups_data = []
    for data in db.session.query(Group).all():
        if data.is_private == False:
            groups_data.append(
                {'id': int(data.id), 'name': data.name})
    return render_template('groups_private.html', stylesheet='groups', groups_data=groups_data)


@site.route('/group')
@site.route('/group/<int:id>', methods=['GET', 'POST'])
@login_required
def group(id=None):
    """
    Render the groups template on the /group route
    """
    group = Group.query.get_or_404(id)
    return render_template('group.html', stylesheet='group', group=group)


# Session related ################################################################
@site.route('/sessions', methods=['GET', 'POST'])
@login_required
def sessions():
    """
    Render the sessions template on the /sessions route
    """
    return render_template('sessions.html', stylesheet='sessions')


@site.route('/session', methods=['GET', 'POST'])
@login_required
def session():
    """
    Render the session template on the /session route
    """
    return render_template('session.html', stylesheet='session')


@site.route('/organize_session', methods=['GET', 'POST'])
@login_required
def organize_session():
    """
    Render the organize_session template on the /organize_session route
    """
    return render_template('organize_session.html', stylesheet='organize_session')


@site.route('/game', methods=['GET', 'POST'])
@login_required
def game():
    """
    Render the game template on the /game route
    """
    return render_template('game.html', stylesheet='game')


@site.route('/add-games', methods=['GET', 'POST'])
@login_required
def add_games():
    """
    Render the add-games template on the /add-games route
    """
    form = GamesSearchForm()
    for data in db.session.query(Game).all():
        form.title.choices.append(data.title)
        if data.publication_year not in form.years.choices:
            form.years.choices.append(data.publication_year)
        if data.min_players not in form.min_players.choices:
            form.min_players.choices.append(data.min_players)
        if data.max_players not in form.max_players.choices:
            form.max_players.choices.append(data.max_players)
        if data.min_playtime not in form.min_playtime.choices and data.min_playtime not in form.max_playtime.choices:
            form.min_playtime.choices.append(data.min_playtime)
            form.max_playtime.choices.append(data.min_playtime)
    form.years.choices.sort()
    form.min_players.choices.sort()
    form.max_players.choices.sort()
    form.min_playtime.choices.sort()
    form.max_playtime.choices.sort()
    form.title.choices.insert(0, 'Aucun')
    form.years.choices.insert(0, 'Aucune')
    form.min_players.choices.insert(0, 'Aucun')
    form.max_players.choices.insert(0, 'Aucun')
    form.min_playtime.choices.insert(0, 'Aucune')
    form.max_playtime.choices.insert(0, 'Aucune')
    if form.validate_on_submit():
        researched_game = Game.query.filter_by(title=form.title.data).first()
        print(researched_game)
        return render_template('add-games.html', form=form, stylesheet='add-games', researched_game=researched_game)
    return render_template('add-games.html', stylesheet='add-games', form=form)


@site.route('/edit-games', methods=['GET', 'POST'])
@login_required
def edit_games():
    """
    Render the edit-games template on the /edit-games route
    """
    form = UpdateInformationForm()
    if form.validate_on_submit():
        return redirect(url_for('site.edit-games'))
    return render_template('edit-games.html', stylesheet='edit-games', form=form)
