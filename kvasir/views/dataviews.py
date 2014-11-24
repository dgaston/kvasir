from flask import render_template, flash, redirect, url_for, g
from flask.ext.login import login_required

from kvasir import app, models
from kvasir.forms import *

from bson.objectid import ObjectId

@app.route('/search', methods = ['POST'])
@login_required
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query = g.search_form.search.data))

#This routine needs to be re-written and simplified to be brought in to line with
#MongoDB queries as well as better integrate searching functions and ordering of returned results
@app.route('/search_results/<query>')
@login_required
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
    elif query.startswith("rs"):
        results = models.Marker.objects(dbsnp_id__contains=query)
        type = 'marker'
    else:
        results = models.Gene.objects(hgnc_ids__contains=query)
        type = 'gene'
        
    return render_template('search_results.html', results = results, type = type)

@app.route('/gene/<id>')
@login_required
def gene(id):
    g = models.Gene.objects.get(ensembl_id=id)
    
    if g == None:
        flash('Gene ' + id + ' not found.')
        return redirect(url_for('index'))
        
    return render_template('gene.html', gene = g)

@app.route('/panels')
@login_required
def panels():
    p = models.GeneList.objects

    return render_template('panels.html', panels = p)

@app.route('/marker/<id>')
@login_required
def marker(id):
    m = models.Marker.objects.get(dbsnp_id=id)
    
    if m == None:
        flash('Marker ' + id + ' not found.')
        return redirect(url_for('index'))
        
    return render_template('marker.html', marker = m)

@app.route('/allele/<marker>/<id>')
@login_required
def allele(marker, id):
    m = models.Marker.objects.get(dbsnp_id=marker)
    
    i = 0
    index = 0
    for allele in m.alleles:
        if allele.id == id:
            index = i
            break
        i = i + 1
    
    a = m.alleles[index]
    
    if a == None:
        flash('Allele ' + id + ' not found.')
        return redirect(url_for('index'))
        
    return render_template('allele.html', allele = a, marker = m)

@app.route('/association/<marker>/<id>', methods = ['GET', 'POST'])
@login_required
def association(marker, id):
    m = models.Marker.objects.get(dbsnp_id=marker)
    
    i = 0
    index = 0
    for association in m.associations:
        if association.id == id:
            index = i
            break
        i = i + 1
    
    a = m.associations[index]
    
    if a == None:
        flash('Association ' + id + ' not found.')
        return redirect(url_for('index'))
    
    form = NoteForm()
    if form.validate_on_submit():
        n = models.AssociationComment(author = g.user.nickname, body = form.note.data)
        a.comments.append(n)
        m.save()
        
    return render_template('association.html', association = a, marker = m, form = form)

@app.route('/active_associations/<project>', methods = ['GET', 'POST'])
@login_required
def active_associations(project):
    p = models.Project.objects.get(project_name=project)

    return render_template('active_associations.html', project = p)