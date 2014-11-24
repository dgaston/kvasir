from flask import g

from flask.ext import admin
from flask.ext.admin.contrib.mongoengine import ModelView

# Customized admin views
from kvasir import db


class MyModelView(ModelView):
    def is_accessible(self):
        return g.user.is_admin()

class MyAdminIndexView(admin.AdminIndexView):
    def is_accessible(self):
        return g.user.is_admin()

class UserView(MyModelView):
    column_filters = ['nickname', 'email']
    column_searchable_list = ('nickname', 'email', 'slug')
    
    def _feed_user_choices(self, form):
        users = db.user.find(fields=('name',))
        form.user_id.choices = [(str(x['_id']), x['name']) for x in users]
        return form
    
    #def create_form(self):
    #    form = super(UserView, self).create_form()
    #    return self._feed_user_choices(form)
    #
    #def edit_form(self, obj):
    #    form = super(User, self).edit_form(obj)
    #    return self._feed_user_choices(form)

class SampleView(MyModelView):
    column_filters = ['sample_id', 'phenotypes', 'status']
    column_searchable_list = ('sample_id', 'phenotypes')
    