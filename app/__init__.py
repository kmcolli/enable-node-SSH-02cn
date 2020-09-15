from flask import Flask
import os, logging, datetime, requests, fileinput, urllib, json
from logging.config import dictConfig
from logdna import LogDNAHandler
from app.config import Config

dictConfig({
            'version': 1,
            'formatters': {
                'default': {
                    'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                }
            },
            'handlers': {
                'logdna': {
                    'level': logging.DEBUG,
                    'class': 'logging.handlers.LogDNAHandler',
                    'key': os.environ.get('LOGDNA_APIKEY'),
                    'options': {
                        'app': 'enable-node-ssh-02cn.py',
                        'tags': os.environ.get('SERVERNAME'),
                        'env': os.environ.get('ENVIRONMENT'),
                        'url': os.environ.get('LOGDNA_LOGHOST'),
                        'index_meta': True,
                        'include_standard_meta': True,
                    },
                 },
            },
            'root': {
                'level': logging.DEBUG,
                'handlers': ['logdna']
            }
        })

app = Flask(__name__)
app.config.from_object(Config)

from app import routes

app.logger.info("Starting zero to cloud native enable node SSH.")