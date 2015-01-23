from flask import render_template, flash, redirect, url_for, g
from flask.ext.login import login_required
from flask.ext.security import roles_accepted

from kvasir import app, models
from kvasir.forms import *

from bson.objectid import ObjectId
from mongoengine import Q

import datetime

from kvasir.models import User

# @roles_accepted('Editor', 'GroupLeader')

@app.route('/addtask', methods=['GET', 'POST'])
@login_required
@roles_accepted('GroupLeader', 'Admin')
def addtask():
    form = TaskForm()

    if form.validate_on_submit():
        u = User.objects.get(email=g.user.email)
        a = User.objects.get(email=form.assigned.data)

        p = Project.objects.get(slug=form.project.data)

        t = models.Task(assigned_by_user=u, assigned_user=a, project=p,
                        priority=form.priority.data, description=form.description.data)

        t.save()

        a.tasks.append(t)
        p.tasks.append(t)

        a.save()
        p.save()

        flash('Your task has been added')
        return redirect(url_for('user', email=a.email))

    return render_template('addtask.html', form=form)

# This still needs to be adjusted from user data to sample data
@app.route('/addsample/<id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor', 'GroupLeader', 'Admin')
def addsample(id):
    form = AddSampleForm()
    if form.validate_on_submit():
        s = models.Sample(sample_id_string=form.sample_id.data, maternal_id_string=form.maternal_id.data,
                          paternal_id_string=form.paternal_id.data, status=form.status.data, project_id=id,
                          ngs_sequencing=form.ngs.data, genotype_data=form.genotyping.data,
                          phenotypes=form.phenotypes.data, variants_discovered=form.variants.data)
        s.save()
        flash('Your changes have been saved.')
        return redirect(url_for('project', id=id))
    else:
        #Need to change this to better handle errors
        return render_template('addsample.html', form=form)

    return render_template('addsample.html', form=form)

@app.route('/add_gene_summary/<id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor', 'GroupLeader')
def add_gene_summary(id):
    g = models.Gene.objects.get(ensembl_id=id)

    if g == None:
        flash('Gene ' + id + ' not found.')
        return redirect(url_for('index'))

    form = GeneSummaryForm()

    if form.validate_on_submit():
        oid = ObjectId()
        s_oid = str(oid)

        s = models.GeneSummary(id=s_oid, type=form.type.data, text=form.text.data)
        g.summaries.append(s)
        g.save()
        return redirect(url_for('gene', id=g.ensembl_id))

    return render_template('addgenesummary.html', gene=g, form=form)


@app.route('/editgenesummary/<gene>/<id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor')
def editgenesummary(gene, id):
    form = GeneSummaryForm()
    g = models.Gene.objects.get(ensembl_id=gene)

    i = 0
    index = 0
    for summary in g.summaries:
        if summary.id == id:
            index = i
            break
        i = i + 1

    s = g.summaries[index]

    if s == None:
        flash('Summary ' + id + ' not found.')
        return redirect(url_for('index'))

    if form.validate_on_submit():
        models.Gene.objects(Q(ensembl_id=gene) & Q(summaries__id=id )).update_one(
            set__summaries__S__type=form.type.data)
        models.Gene.objects(Q(ensembl_id=gene) & Q(summaries__id=id )).update_one(
            set__summaries__S__text=form.text.data)

        g.reload()

        flash('Your changes have been saved.')
        return redirect(url_for('gene', id=g.ensembl_id))
    else:
        form.type.data = s.type
        form.text.data = s.text

    return render_template('editgenesummary.html', form=form, gene=g)
