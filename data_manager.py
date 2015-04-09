#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, datetime, csv, time

from flask.ext.script import Manager, Server, Command, Option, prompt_bool
from flask.ext.security.utils import encrypt_password

from kvasir import app, db, models, user_datastore, security
from config import *
from collections import defaultdict
from bson.objectid import ObjectId

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
source_dir = os.path.dirname(os.path.realpath(__file__))

data_manager = Manager(app)

@data_manager.option('-i', '--id', dest='id', help='sample id')
@data_manager.option('-x', '--maternal_id', dest='mid', help='maternal sample id', default="None")
@data_manager.option('-y', '--paternal_id', dest='pid', help='paternal sample id', default="None")
@data_manager.option('-s', '--status', dest='status', help='affected status (affected, unaffected, unknown)')
@data_manager.option('-p', '--project', dest='project_id', help='project id')
@data_manager.option('-e', '--exome', dest='exome_dir', help='Directory of exome sequencing data')
@data_manager.option('-g', '--genotype', dest='genotype_dir', help='Directory with genotype data')
@data_manager.option('-t', '--phenotype', dest='phenotype_string', help='Comma seperated list of human phenotype ontology terms for patient sample (No spaces between commas)', default=None)
def add_sample(id, mid, pid, status, project_id, exome_dir, genotype_dir, phenotype_string):
    "Add an individual sample to the project database"
    
    project = models.Project.query.filter_by(project_name = project_id).first()
    
    sys.stdout.write("Adding sample to table: \n")
    
    try:
        s = models.Sample.objects.get()
    except:
        s = models.Sample(sample_id_string=id, maternal_id_string=mid, paternal_id_string=pid, status=status, project_id=project.id, ngs_sequencing=exome_dir, genotype_data=genotype_dir, phenotypes=phenotype_string, variants_discovered="None")
    else:
        sys.stderr.write("ERROR: Sample with id string %s already exists in database. Exiting\n" % id)
        sys.exit()
    
    s.save()

@data_manager.option('-f', '--file', dest='file', help='Samples file')
def populate_samples(file):
    "Populate info for multiple samples from a tab-delimited file"
    
    with open(file, 'rU') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            s = models.Samples(id=row[id], maternal_id=row[mid], paternal_id=row[pid], status=row[status], project=row[project], exome=row[exome_dir], genotype_data=row[genotype_dir], phenotypes=row[phenotypes])
            db.session.add(o)
        db.session.commit()

@data_manager.option('-u', '--user', dest='user', help='User Email')
@data_manager.option('-p', '--project', dest='project', help='Project ID')
@data_manager.option('-s', '--subject', dest='subject', help='Subject')
@data_manager.option('-b', '--body', dest='body', help='Body')
def add_note(user, subject, body, project):
    u = models.User.objects.get(email=user)
    
    n = models.Note(project_id=project, user=u, subject=subject, body=body, posted = datetime.date.today())
    n.save()

@data_manager.option('-p', '--project', dest='project', help='Project Name')
@data_manager.option('-f', '--file', dest='file', help='Full path to the database file')
@data_manager.option('-n', '--name', dest='name', help='A short name for the database')
def add_GDB(project, file, name):
    p = models.Project.objects.get(project_name=project)
    g = models.GDatabase(file = file, short_name = name)
    g.projects.append(p)
    g.save()
    
    g.slug = str(g.id)
    g.save()
    
    p.gemini_databases.append(g)
    p.save()

@data_manager.option('-n', '--name', dest='name', help='Project Name')
def create_project(name, type):
    project = models.Project(project_name=name, slug=name)
    project.save()

@data_manager.option('-p', '--project', dest='project', help='Project ID')
def delete_project(project):
    "Delete a specified project from the database. Does not remove directory or data"
    
    project = models.Project.objects.get(project_name = project)
    
    sys.stdout.write("Deleting project: %s (ID: %s)\n" % (project.project_name, project.id))
    
    project.delete()

if __name__ == "__main__":
    data_manager.run()