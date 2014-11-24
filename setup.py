from setuptools import setup

setup(name='Kvasir',
      version='0.9',
      description='Kvasir OpenShift App',
      author='Dan Gaston',
      author_email='admin@deaddriftbio.com',
      url='https://www.python.org/community/sigs/current/distutils-sig',
      install_requires=['Flask', 'MarkupSafe', 'Flask-MongoEngine', 'Flask-Script',
                        'numpy', 'Flask-OpenID', 'Cython', 'Flask-Login', 'Flask-Mail',
                        'pytz', 'pyzmq', 'scipy', 'gemini'],
     )
