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

user_manager = Manager(app)

@user_manager.option('-n', '--nickname', dest='nick', help='User Nickname')
@user_manager.option('-e', '--email', dest='email', help='User Email Address')
@user_manager.option('-p', '--password', dest='password', help='User Password')
def create_user(nick, email, password):
    user_datastore.create_user(email=email, password=encrypt_password(password), nickname=nick)

@user_manager.option('-e', '--email', dest='email', help='User Email Address')
def delete_user(email):
    user = models.User.objects.get(email=email)
    user.datastore.delete_user(user)

@user_manager.option('-e', '--email', dest='email', help='User Email Address')
@user_manager.option('-r', '--role', dest='role_name', help='Role to add')
def add_role_to_user(email, role_name):
    user = models.User.objects.get(email=email)
    role = models.Role.objects.get(name=role_name)
    
    user.roles.append(role)
    user.save()

@user_manager.option('-r', '--role', dest='role_name', help='Name of role to add')
@user_manager.option('-d', '--desc', dest='desc', help='Description of role')
def create_user_role(role_name, desc):
    role = models.Role(name=role_name, description=desc)
    role.save()

@user_manager.option('-e' '--email', dest='email', help='Users email address')
@user_manager.option('-p', '--project', dest='project', help='Project name')
def add_project_to_user(email, project):
    project = models.Project.objects.get(project_name=project)
    user = models.User.objects.get(email=email)
    
    user.projects.append(project)
    user.save()

if __name__ == "__main__":
    user_manager.run()