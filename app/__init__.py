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

iamhost=os.environ.get("UTILITY_02CN_SERVICE_SERVICE_HOST")
iamport=os.environ.get("UTILITY_02CN_SERVICE_SERVICE_PORT")
iam_url="http://"+iamhost+":"+iamport+"/api/v1/getiamtoken/"
iam_data = { "apikey":  app.config["IBMCLOUD_APIKEY"]}
headers = { "Content-Type": "application/json" }
resp = requests.get(iam_url, data=json.dumps(iam_data), headers=headers)
iamtoken = resp.json()["iamtoken"]    
app.logger.info("iamtoken = {}".format(iamtoken))        
certManagerEndpoint = app.config['CERT_MANAGER_ENDPOINT']
header = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + iamtoken["access_token"]
}
rabbit_crn = app.config['RABBITMQ_CERT_CRN']

url = certManagerEndpoint+'/api/v2/certificate/'+urllib.parse.quote_plus(rabbit_crn)
app.logger.info("url = {}".format(url)) 
response = requests.get(url,headers=header)
json_response = json.loads(response.text)
app.logger.info("JSON Response {}".format(json_response))
app.logger.info("cert file {}".format(json_response['data']['content']))
cert_file = open("rabbit-crt.pem", "wt")
n = cert_file.write(json_response['data']['content'])
cert_file.close()

from app import routes

app.logger.info("Started enable node SSH 02cn process.")