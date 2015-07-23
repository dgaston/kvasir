import sys
import hashlib
import json
import os
import datetime

from flask import render_template
from flask import flash
from flask import redirect
from flask import url_for
from flask import jsonify
from flask import request
from flask import make_response
from flask import session
from flask import g

from flask.ext.login import login_required
from flask.ext.security import roles_accepted

from kvasir import app, models
from kvasir.forms import *
import kvasir.kmethods as kmethods
from config import STATIC_FOLDER

from bson.objectid import ObjectId

from celery.result import AsyncResult

from gemini import GeminiQuery

@app.route('/gemini_query/<project>/<id>', methods = ['GET', 'POST'])
@login_required
@roles_accepted('User', 'Admin')
def gemini_query(project, id):
    
    gdb = models.GDatabase.objects.get(id = ObjectId(id))
    if gdb == None:
        flash('Database ' + id + ' not found.')
        return redirect(url_for('index'))
    
    form = GQueryForm()

    if form.validate_on_submit():
        #build query
        (query, genotype_filter) = kmethods.build_gemini_query_web(form)

        mode = form.mode.data

        results_string = "results_%s_%s_%s_%s" % (mode, id, hashlib.md5(query).hexdigest(), hashlib.md5(genotype_filter).hexdigest())
        json_filename = "%s.json" % (results_string)

        celery_result = kmethods.run_gemini_query.delay(id, query, genotype_filter, json_filename, mode, results_string, g.user.id)

        return redirect(url_for('loading', task_id=celery_result.id))

    print form.errors
    gq = GeminiQuery(gdb.file)
    gq.run("select * from samples")
    
    samples = []
    for row in gq:
        samples.append(row)
    
    project = models.Project.objects.get(slug=project)

    num_rows = len(models.GeneList.objects())
        
    return render_template('gemini_query.html', database = gdb, samples = samples,
                           project = project, project_samples = project.samples,
                           form = form, dbid = id, num_rows = num_rows)


@app.route('/export/<file_name>')
@login_required
@roles_accepted('User', 'Admin')
def export(file_name):
    try:
        #header = session.pop('header')
        header = session['header']
    except KeyError:
        sys.stderr.write("ERROR: value for header not found in session object")

    #session.pop('js_header')
    file = "%s.json" % file_name
    json_results_fh = os.path.join(STATIC_FOLDER, file)

    with open(json_results_fh) as json_data:
        data = json.load(json_data)

    output = []
    output.append("\t".join(header))

    for row in data['data']:
        outrow = []
        for name in header:
            if row[name]:
                outrow.append(str(row[name]))
            else:
                outrow.append("")
        output.append("\t".join(outrow))

    output_string = "\n".join(output)
    response = make_response(output_string)

    response.headers["Content-Disposition"] = "attachment; filename=%s.txt" % file_name
    return response

@app.route('/analytics/<file_name>')
@login_required
@roles_accepted('User', 'Admin')
def analytics(file_name):
    header = ""
    try:
        #header = session.pop('header')
        header = session['header']
    except KeyError:
        sys.stderr.write("ERROR: value for header not found in session object")
    else:
        header = ""

    js_header = ""
    try:
        #js_header = session.pop('js_header')
        js_header = session['js_header']
    except KeyError:
        sys.stderr.write("ERROR: value for js_header not found in session object")
    else:
        js_header = ""

    file = "%s.json" % file_name
    results_file = "/static/%s" % file
    json_results_fh = os.path.join(STATIC_FOLDER, file)

    return render_template('analytics.html', file=results_file, header=header, js_header=js_header)


@app.route('/loading/<task_id>')
@login_required
@roles_accepted('User', 'Admin')
def loading(task_id):
    sys.stderr.write("DEBUG: Loading Page\n")
    return render_template('loading.html', task_id=task_id)


@app.route('/view_result/<task_id>')
@login_required
@roles_accepted('User', 'Admin')
def view_result(task_id):
    sys.stderr.write("DEBUG: Viewing Result\n")

    try:
        result = AsyncResult(task_id)
    except:
        sys.stderr.write("DEBUG: Unexpected error: %s\n" % (sys.exc_info()[0]))
        raise

    try:
        (header, js_header, results_file, gdb_file, query, genotype_filter, results_string, json_results_fh) = result.get()
    except:
        sys.stderr.write("DEBUG:Error when fetching data with result.get()\n")
        print result.traceback
        return render_template('500.html')

    session['header'] = header
    session['js_header'] = js_header

    return render_template('gemini_query_result.html', file = gdb_file, query = query,
                       genotype_filter = genotype_filter, header = header,
                       js_header = js_header, results_file = results_file, results_string=results_string)


@app.route('/poll_state', methods = ['GET', 'POST'])
@login_required
@roles_accepted('User', 'Admin')
def poll_state():
    sys.stderr.write("DEBUG: Polling Results: Getting Task ID from Request Form\n")
    task_id = request.form['task_id']

    sys.stderr.write("DEBUG: Polling Results: Getting ASyncResult\n")

    try:
        task = AsyncResult(task_id)
    except:
        sys.stderr.write("Unexpected error: %s\n" % (sys.exc_info()[0]))
        raise

    sys.stderr.write("DEBUG: Polling Results: Checking Task State\n")
    if task.state == 'PENDING':
        #job did not start yet
        sys.stderr.write("DEBUG: Status is Pending\n")
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state == 'PROGRESS':
        sys.stderr.write("DEBUG: Task Identified as in progress\n")
        response = {
            'state': task.state,
        }
    elif task.state == 'SUCCESS':
        sys.stderr.write("DEBUG: Task Identified as Successful\n")
        sys.stderr.write("DEBUG: State: %s\n" % task.state)
        sys.stderr.write("DEBUG: URL: %s\n" % url_for('view_result', task_id=task_id))
        response = {
            'state': task.state,
            'url': url_for('view_result', task_id=task_id)
        }
        sys.stderr.write("DEBUG: Response is:\n%s\n\n" % jsonify(response))
    elif task.state == 'FAILURE':
        # something went wrong in the background job
        sys.stderr.write("DEBUG: Task Failed with Traceback: %s\n" % (task.traceback))
        response = {
            'state': task.state,
            'status': str(task.traceback),
            'url': url_for('500.html')
        }
    else:
        #Unknown Task State
        sys.stderr.write("DEBUG: Unknown task State\n")
        response = {
            'state': task.state,
            'status': str(task.traceback),  # this is the exception raised
            'url': url_for('500.html')
        }

    sys.stderr.write("DEBUG: Sending JSON of Response\n")
    return jsonify(response)


    #Old Code
    # """ A view to report the progress to the user """
    # data = 'Fail'
    # url = 'None'
    # sys.stderr.write("Polling task ID: %s\n" % request.form['task_id'])
    # if request.form['task_id']:
    #     task_id = request.form['task_id']
    #     result = AsyncResult(task_id)
    #
    #     if result.ready() == True:
    #         sys.stderr.write("Result Ready\n")
    #         data = "Completed"
    #         url = url_for('view_result', task_id=task_id)
    #     else:
    #         #data = result.state
    #         data = "Running"
    # else:
    #     data = 'No task_id in the request'
    #
    # return jsonify(data=data, url=url)