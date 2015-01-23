from flask import render_template, flash, redirect, url_for, g
from flask.ext.login import login_required
from flask.ext.security import roles_accepted

from kvasir import app, models
from kvasir.forms import *

from bson.objectid import ObjectId

@app.route('/search', methods = ['POST'])
@login_required
@roles_accepted('User', 'Admin')
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query = g.search_form.search.data))

#This routine needs to be re-written and simplified to be brought in to line with
#MongoDB queries as well as better integrate searching functions and ordering of returned results
@app.route('/search_results/<query>')
@login_required
@roles_accepted('User', 'Admin')
def search_results(query):
    
    if query.startswith("ENSG"):
        results = models.Gene.objects(ensembl_id__contains=query)
        type = 'gene'
    elif query.startswith("LRG_"):
        results = models.Gene.objects(ensembl_id__contains=query)
        type = 'gene'
    elif query.startswith("CCDS"):
        results = models.Gene.objects(ccds_ids__contains=query)
        type = 'gene'
    else:
        results = models.Gene.objects(hgnc_ids__contains=query)
        type = 'gene'
        
    return render_template('search_results.html', results = results, type = type)

@app.route('/gene/<id>')
@login_required
@roles_accepted('User', 'Admin')
def gene(id):
    g = models.Gene.objects.get(ensembl_id=id)
    
    if g == None:
        flash('Gene ' + id + ' not found.')
        return redirect(url_for('index'))
        
    return render_template('gene.html', gene = g)

@app.route('/panels')
@login_required
@roles_accepted('User', 'Admin')
def panels():
    p = models.GeneList.objects

    return render_template('panels.html', panels = p)
