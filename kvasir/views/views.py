from flask import render_template, flash, redirect, url_for, request, g, send_from_directory
from flask.ext.login import current_user, login_required
from flask.ext.security import roles_accepted

from bson.objectid import ObjectId

from kvasir import app, models
from kvasir.forms import *
from config import *

import datetime, os

from kvasir.models import User
from werkzeug import secure_filename

@app.before_request
def before_request():
    g.user = current_user
    projects = models.Project.objects
    users = models.User.objects
    g.projects = projects
    g.users = users
    
    if g.user.is_authenticated():
        user = User.objects.get(id=g.user.id)
        user.last_seen = datetime.date.today()
        user.save()
        g.search_form = SearchForm()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
@app.route('/index')
@login_required
def index():
    projects = models.Project.objects
    users = models.User.objects
    
    return render_template('index.html', title = 'Home', user = g.user, projects = projects, users = users)
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/project/<slug>',  methods = ['GET', 'POST'])
@login_required
@roles_accepted('User', 'Admin')
def project(slug):
    project = models.Project.objects.get(slug=slug)
    users = models.User.objects
    
    if project == None:
        flash('Project ' + project.project_name + ' not found.')
        return redirect(url_for('index'))
    
    form = NoteForm()
    if form.validate_on_submit():
        
        user = models.User.objects.get(email=g.user.email)
        n = models.Note(body = form.note.data, posted = datetime.date.today(), user = user)
        project.notes.append(n)
        project.save()
        flash('Your note has been added.')
        return redirect(url_for('project', slug=project.slug))
        
    return render_template('project.html', project=project, users=users, id=id, form=form)

@app.route('/upload/<name>', methods = ['GET', 'POST'])
@login_required
@roles_accepted('User', 'Admin')
def upload(name):
    form = FileForm()
    if request.method == 'POST':
        file = request.files['fileName']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            print filename
            print filepath
            
            oid = ObjectId()
            s_oid = str(oid)
            
            user = models.User.objects.get(email=g.user.email)
            f = models.File(uploaded_by = user, location = filepath, filename = filename)
            f.save()
            
            project = models.Project.objects.get(slug=name)
            project.files.append(f)
            project.save()
            
            flash('Your file has been uploaded.')
            return redirect(url_for('project', slug = project.slug))
        
    return render_template('upload.html', id = id, form = form)

@app.route('/download/<project>/<id>/', methods=['GET', 'POST'])
@login_required
@roles_accepted('User', 'Admin')
def download(project, id):
    p = models.Project.objects.get(slug=project)
    
    i = 0
    for file in p.files:
        if file.id == id:
            findex = i
            break
        i = i + 1
    
    f = p.files[findex]
    
    if f == None:
        flash('File ' + id + ' not found.')
        return redirect(url_for('index'))

    return send_from_directory(app.config['UPLOAD_FOLDER'], f.filename)

@app.route('/file/<project>/<id>', methods = ['GET', 'POST'])
@login_required
@roles_accepted('User', 'Admin')
def file(project, id):
    p = models.Project.objects.get(slug=project)
    
    i = 0
    for file in p.files:
        if file.id == id:
            findex = i
            break
        i = i + 1
    
    f = p.files[findex]
    
    if f == None:
        flash('File ' + id + ' not found.')
        return redirect(url_for('index'))
    
    form = FileNoteForm()
    if form.validate_on_submit():
        user = models.User.objects.get(email=g.user.email)
        n = models.FileNote(body = form.file_note.data, posted = datetime.date.today(), user = user)
        f.file_notes.append(n)
        p.save()
        
        flash('Your note has been added.')
        return redirect(url_for('file', project = p.slug, id = f.id))
    
    return render_template('file.html', project = p, file = f, notes = f.file_notes, form = form)
    
@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html')

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html')
