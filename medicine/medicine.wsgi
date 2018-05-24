#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/home/tmu/medicine/medicine/")  #你app的目录

from medicine.flask_app import app as application