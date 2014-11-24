#!/usr/bin/env python
import os
from kvasir import app

port = int(os.environ.get('PORT', 5000))
app.run(host='localhost', port=port, debug = True)