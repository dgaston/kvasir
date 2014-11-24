FROM ubuntu:14.04
MAINTAINER Dan Gaston <admin@deaddriftbio.com>
RUN sudo apt-get -qq update
RUN sudo apt-get -qqy install python python-dev gettext python-pip zlib1g zlib1g-dev libblas3 libblas-dev liblapack3 liblapack-dev gfortran python-numpy python-scipy git

RUN sudo pip install virtualenv
RUN virtualenv env
RUN source env/bin/activate

RUN pip install uwsgi
RUN pip install -U cython
RUN pip install gemini --allow-external python-graph-core --allow-unverified python-graph-core --allow-external python-graph-dot --allow-unverified python-graph-dot
RUN git clone https://github.com/dgaston/kvasir-mongodb

WORKDIR /kvasir-mongodb
RUN pip install -r requirements.txt
RUN mkdir -p tmp/

# Create a directory for the UNIX sockets
#RUN sudo -p mkdir /var/run/flask-uwsgi
#RUN sudo chown www-data:www-data /var/run/flask-uwsgi

# Create a directory for the logs
#RUN sudo mkdir -p /var/log/flask-uwsgi
#RUN sudo chown www-data:www-data /var/log/flask-uwsgi

# Create a directory for the configs
#RUN sudo mkdir -p /etc/flask-uwsgi
