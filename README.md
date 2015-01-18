kvasir
======
Kvasir is intended as both a light projects database for human genomics (or other model organism) resequencing data and as a 
web-based front-end for the excellent annotation and SQLite Genomics Database system GEMINI. Above all I wanted to make an 
easy to use website to interface with GEMINI databases, with a focus on users who have no idea how to write SQL queries. 

While that often emans anticipating everything possible a user may want to do (which isn't possible) I have tried to make the
program as flexible as possible in that regard. From selecting sampes, phenotypes, genotypes, allele frequency restrictions, etc.

Over time I hope to develop even more tools to easily manipulate and explore genomics data through GEMINI. I am
more than happy to try and accomodate feature requests. 

And of course, please send bug reports!

Kvasir is released under the MIT license.

Installation:

It is suggested you install all python requirements inside an isolated python environment using conda or virtualenv.
In addition you may need the following system packages instaleld:
    1. python-dev (on Ubuntu). This is required for hashlib and several other packages
    2. Mongodb
    3. lapack/blas (liblapack-dev and libblas-dev on ubuntu)
    4. fortran compiler (gfortran)
    5. zlib.h (zlib1g-dev)
    6. tcl8.5
    7. Redis: 


1. pip install --allow-external python-graph-core --allow-unverified python-graph-core python-graph-core
2. pip install --allow-external python-graph-dot --allow-unverified python-graph-dot python-graph-dot
3. install PyVCF
4. pip install -U cython
5. pip install -r requirements.txt


Make sure to modify your config.py file to set up a random string for the SECRET_KEY variable for hashing and salting of passwords in the user management module. If possible you should also configure the mail settings to allow the application to send out emails in case of problems (this feature is not yet fully developed).

To get the web application up and running I prefer to use uWSGI in combination with NGINX. To figure out how to set this up
I used Digital Ocean's excellent tutorials. For uWSHI and NGINX in general:

https://www.digitalocean.com/community/tutorials/how-to-deploy-python-wsgi-applications-using-uwsgi-web-server-with-nginx

You can ignore most of this tutorial other if you already have an isolated python environment set up. I also have created uwsgi scripts for the application (and for starting uwsgi) to work properly with flask. You can modify settings here as needed. But you will need to configure the NGINX server appropriately.

To start the application run the start_celery and start_uwsgi scripts.

#Creating the database

The database is currently set up from a mix of downloaded files from various sources. Each datatype can be loaded into MongoDB
using functions provided in the database scripts. For ease of use I have also created database "dumps" of the core tables which
can be imported into a fresh database using mongorestore.
