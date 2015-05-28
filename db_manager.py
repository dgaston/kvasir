#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import sys

from flask.ext.script import Manager
from flask.ext.security.utils import encrypt_password

from kvasir import app, models, user_datastore
from config import *

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
source_dir = os.path.dirname(os.path.realpath(__file__))

db_manager = Manager(app)

@db_manager.option('-i', '--id', dest='id', help='sample id')
@db_manager.option('-x', '--maternal_id', dest='mid', help='maternal sample id', default="None")
@db_manager.option('-y', '--paternal_id', dest='pid', help='paternal sample id', default="None")
@db_manager.option('-s', '--status', dest='status', help='affected status (affected, unaffected, unknown)')
@db_manager.option('-p', '--project', dest='project_id', help='project id')
@db_manager.option('-e', '--exome', dest='exome_dir', help='Directory of exome sequencing data')
@db_manager.option('-g', '--genotype', dest='genotype_dir', help='Directory with genotype data')
@db_manager.option('-t', '--phenotype', dest='phenotype_string', help='Comma seperated list of human phenotype ontology terms for patient sample (No spaces between commas)', default=None)
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

@db_manager.option('-u', '--user', dest='user', help='User Email')
@db_manager.option('-p', '--project', dest='project', help='Project ID')
@db_manager.option('-s', '--subject', dest='subject', help='Subject')
@db_manager.option('-b', '--body', dest='body', help='Body')
def add_note(user, subject, body, project):
    u = models.User.objects.get(email=user)
    
    n = models.Note(project_id=project, user=u, subject=subject, body=body, posted = datetime.date.today())
    n.save()

@db_manager.option('-n', '--nickname', dest='nick', help='User Nickname')
@db_manager.option('-e', '--email', dest='email', help='User Email Address')
@db_manager.option('-p', '--password', dest='password', help='User Password')
def create_user(nick, email, password):
    user_datastore.create_user(email=email, password=encrypt_password(password), nickname=nick)

@db_manager.option('-e', '--email', dest='email', help='User Email Address')
@db_manager.option('-r', '--role', dest='role_name', help='Role to add')
def add_user_role(email, role_name):
    user = models.User.objects.get(email=email)
    role = models.Role.objects.get(name=role_name)
    
    user.roles.append(role)
    user.save()

@db_manager.option('-n', '--name', dest='name', help='Project Name')
def create_project(name):
    project = models.Project(project_name=name, slug=name)
    project.save()

@db_manager.option('-r', '--role', dest='role_name', help='Name of role to add')
@db_manager.option('-d', '--desc', dest='desc', help='Description of role')
def add_role(role_name, desc):
    role = models.Role(name=role_name, description=desc)
    role.save()
    
@db_manager.option('-p', '--project', dest='project', help='Project ID')
def delete_project(project):
    "Delete a specified project from the database. Does not remove directory or data"
    
    project = models.Project.objects.get(project_name = project)
    
    sys.stdout.write("Deleting project: %s (ID: %s)\n" % (project.project_name, project.id))
    
    project.delete()

if __name__ == "__main__":
    db_manager.run()