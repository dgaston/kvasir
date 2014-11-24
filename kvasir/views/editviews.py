from flask import render_template, flash, redirect, url_for, g
from flask.ext.login import login_required
from flask.ext.security import roles_accepted

from kvasir import app, models
from kvasir.forms import *

from bson.objectid import ObjectId
from mongoengine import Q

import datetime

from kvasir.models import User


@app.route('/addmarker/<name>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor', 'GroupLeader')
def addmarker(name):
    form = MarkerForm()
    if form.validate_on_submit():
        m = models.Marker(dbsnp_id=form.dbsnp_id.data)
        m.save()

        project = models.Project.objects.get(project_name=name)
        project.markers.append(m)
        project.save()

        flash('Your changes have been saved.')
        return redirect(url_for('project', id=id))

    return render_template('addmarker.html', form=form)


@app.route('/addallele/<marker>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor', 'GroupLeader')
def addallele(marker):
    form = AlleleForm()
    m = models.Marker.objects.get(dbsnp_id=marker)

    if form.validate_on_submit():
        oid = ObjectId()
        s_oid = str(oid)

        a = models.Allele(id=s_oid, ref_allele=form.ref_allele.data, alt_allele=form.alt_allele.data,
                          source=form.source.data, orientation=form.orientation.data)

        p = models.Frequency(population="EUR", frequency=form.kg_eur.data)
        a.frequencies.append(p)

        p = models.Frequency(population="AFR", frequency=form.kg_afr.data)
        a.frequencies.append(p)

        p = models.Frequency(population="AMR", frequency=form.kg_amr.data)
        a.frequencies.append(p)

        p = models.Frequency(population="ASN", frequency=form.kg_asn.data)
        a.frequencies.append(p)

        p = models.Frequency(population="ALL", frequency=form.kg_all.data)
        a.frequencies.append(p)

        m.alleles.append(a)
        m.save()

        flash('Your changes have been saved.')
        return redirect(url_for('marker', id=marker))

    return render_template('addallele.html', form=form, marker=m)


@app.route('/addfrequency/<marker>/<id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor', 'GroupLeader')
def addfrequency(marker, id):
    form = FrequencyForm()
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

    if form.validate_on_submit():
        f = models.Frequency(population=form.population.data, frequency=form.frequency.data)
        a.frequencies.append(f)

        m.save()

        flash('Your changes have been saved.')
        return redirect(url_for('allele', marker=m.dbsnp_id, id=a.id))

    return render_template('addfrequency.html', form=form)


@app.route('/addpub/<marker>/<id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor', 'GroupLeader')
def addpub(marker, id):
    form = PublicationForm()
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

    if form.validate_on_submit():
        p = models.Publication(title=form.title.data, abstract=form.abstract.data,
                               pubmed_id=form.pubmed_id.data, doi=form.doi.data)

        p.save()
        a.publications.append(p)
        m.save()

        flash('Your changes have been saved.')
        return redirect(url_for('association', marker=m.dbsnp_id, id=a.id))

    return render_template('addpub.html', form=form)


@app.route('/addassociation/<marker>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor', 'GroupLeader')
def addassociation(marker):
    form = AssociationForm()
    m = models.Marker.objects.get(dbsnp_id=marker)

    if form.validate_on_submit():
        oid = ObjectId()
        s_oid = str(oid)

        p = Project.objects.get(slug=form.project.data)
        u = User.objects.get(email=g.user.email)

        a = models.Association(id=s_oid, allele_of_interest=form.aoi.data, favoured_genotype=form.fg.data,
                               trait=form.trait.data, description=form.desc.data,
                               project=p, last_modified_by=u, active=form.active.data,
                               impact=form.impact.data, confidence=form.confidence.data)

        m.associations.append(a)
        m.save()

        flash('Your changes have been saved.')
        return redirect(url_for('marker', id=marker))

    return render_template('addassociation.html', form=form, marker=m)


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


@app.route('/editassociation/<marker>/<id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor')
def editassociation(marker, id):
    form = EditAssociationForm()
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

    if form.validate_on_submit():
        user = models.User.objects.get(email=g.user.email)
        p = Project.objects.get(slug=form.project.data)
        oid = ObjectId()
        s_oid = str(oid)
        h = models.HistoricalAssociation(id=s_oid, allele_of_interest=a.allele_of_interest,
                                         trait=a.trait, reason=form.reason.data,
                                         project=a.project, active=False, impact=a.impact,
                                         confidence=a.confidence, removed_by=user)

        a.previous_versions.append(h)
        p = models.Project.objects.get(project_name=form.project.data)

        models.Marker.objects(Q(dbsnp_id=marker) & Q(associations__id=id)).update_one(
            set__associations__S__allele_of_interest=form.aoi.data)
        models.Marker.objects(Q(dbsnp_id=marker) & Q(associations__id=id)).update_one(
            set__associations__S__trait=form.trait.data)
        models.Marker.objects(Q(dbsnp_id=marker) & Q(associations__id=id)).update_one(
            set__associations__S__last_modified_by=user)
        models.Marker.objects(Q(dbsnp_id=marker) & Q(associations__id=id)).update_one(
            set__associations__S__last_modified=datetime.datetime.now)
        models.Marker.objects(Q(dbsnp_id=marker) & Q(associations__id=id)).update_one(
            set__associations__S__impact=float(form.impact.data))
        models.Marker.objects(Q(dbsnp_id=marker) & Q(associations__id=id)).update_one(
            set__associations__S__confidence=float(form.confidence.data))
        models.Marker.objects(Q(dbsnp_id=marker) & Q(associations__id=id)).update_one(
            set__associations__S__active=form.active.data)
        models.Marker.objects(Q(dbsnp_id=marker) & Q(associations__id=id)).update_one(
            set__associations__S__project=p)

        if form.active.data == 'True':
            models.Marker.objects(Q(dbsnp_id=marker) & Q(associations__id=id)).update_one(
            set__associations__S__active=True)
        else:
            models.Marker.objects(Q(dbsnp_id=marker) & Q(associations__id=id)).update_one(
            set__associations__S__active=False)

        flash('Your changes have been saved.')

        return redirect(url_for('marker', id=m.dbsnp_id))
    else:
        form.aoi.data = a.allele_of_interest
        form.trait.data = a.trait
        form.desc.data = a.description
        form.active.data = a.active
        form.impact.data = a.impact
        form.confidence.data = a.confidence
        form.reason.data = "Required"

    return render_template('editassociation.html', form=form, marker=m, association=a)


@app.route('/edit_marker/<marker>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor')
def edit_marker(marker):
    form = MarkerForm()

    m = models.Marker.objects.get(dbsnp_id=marker)

    if form.validate_on_submit():
        m.dbsnp_id = form.dbsnp_id.data
        m.save()

        flash('Your changes have been saved.')
        return redirect(url_for('edit_marker', marker=marker.dbsnp_id))
    else:
        form.dbsnp_id.data = m.dbsnp_id

    return render_template('edit_marker.html', form=form)


# This still needs to be adjusted from user data to sample data
@app.route('/addsample/<id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor', 'GroupLeader')
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


@app.route('/add_association_summary/<marker>/<id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor', 'GroupLeader')
def add_association_summary(marker, id):
    m = models.Marker.objects.get(dbsnp_id=marker)

    i = 0
    index = 0
    for association in m.associations:
        if association.id == id:
            index = i
            break
        i += 1

    a = m.associations[index]
    if a == None:
        flash('Association ' + id + ' not found.')
        return redirect(url_for('index'))

    form = AssociationSummaryForm()

    if form.validate_on_submit():
        oid = ObjectId()
        s_oid = str(oid)

        s = models.AssociationSummary(id=s_oid, type=form.type.data, title=form.title.data, text=form.text.data)
        a.summaries.append(s)
        m.save()

        note_form = NoteForm()
        return redirect(url_for('association', marker=m.dbsnp_id, id=a.id, form=note_form))

    return render_template('addassociationsummary.html', association=a, marker=m, form=form)


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

@app.route('/genotypesummary/<marker>', methods=['GET', 'POST'])
@app.route('/genotypesummary/<marker>/<id>', methods=['GET', 'POST'])
@login_required
@roles_accepted('Editor')
def genotypesummary(marker, id=None):
    form = GenotypeSummaryForm()
    m = models.Marker.objects.get(dbsnp_id=marker)

    if id:
        i = 0
        index = 0
        for summary in m.genotype_summaries:
            if summary.id == id:
                index = i
                break
            i = i + 1

        s = m.genotype_summaries[index]

        if form.validate_on_submit():
            models.Marker.objects(Q(dbsnp_id=marker) & Q(genotype_summaries__id=id )).update_one(
                set__genotype_summaries__S__genotype=form.genotype.data)
            models.Marker.objects(Q(dbsnp_id=marker) & Q(genotype_summaries__id=id )).update_one(
                set__genotype_summaries__S__text=form.text.data)

            m.reload()

            flash('Your changes have been saved.')
            return redirect(url_for('marker', id=m.dbsnp_id))
        else:
            form.genotype.data = s.genotype
            form.text.data = s.text

    if form.validate_on_submit():
        oid = ObjectId()
        s_oid = str(oid)

        s = models.GenotypeSummary(id=s_oid, genotype=form.genotype.data, text=form.text.data)
        m.genotype_summaries.append(s)
        m.save()

        flash('Your changes have been saved.')
        return redirect(url_for('marker', id=m.dbsnp_id))

    return render_template('genotypesummary.html', form=form, marker=m)