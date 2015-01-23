from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, login_required
from flask.ext.security import roles_accepted

from kvasir import app, lm
from kvasir.forms import *
from config import *

import glob, os

from kvasir.models import User
@lm.user_loader
def load_user(id):
    return User.objects.get(id=id)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
    
    return redirect(url_for('index'))

def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    try:
        user = User.objects.get(email=resp.email)
    except:
        print "Setting up new user\n"
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname=nickname, email=resp.email)
        user.save()
        
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/logout')
def logout():
    #Clean up all JSON Query result files in the /static directory
    pattern = "%s/results_%s_*.json" % (STATIC_FOLDER, g.user.id)
    result_files = glob.glob(pattern)
    for file in result_files:
        print "Deleting file: %s\n" % file
        os.remove(file)
    logout_user()
    return redirect(url_for('index'))

@app.route('/user/<email>')
@login_required
@roles_accepted('User', 'Admin')
def user(email):
    user = User.objects.get(email=email)
    if user == None:
        flash('User ' + email + ' not found.')
        return redirect(url_for('index'))

    return render_template('user.html', user = user)

@app.route('/edit', methods = ['GET', 'POST'])
@login_required
@roles_accepted('User', 'Admin')
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        
        user = User.objects.get(id=g.user.id)
        user.nickname = g.user.nickname
        user.about_me = g.user.about_me
        user.save()
        
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
        
    return render_template('edit.html', form = form)

