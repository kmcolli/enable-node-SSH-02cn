import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    ENVIRONMENT = os.environ.get("ENVIRONMENT")
    LOGDNA_APIKEY = os.environ.get("LOGDNA_APIKEY")
    LOGDNA_LOGHOST = os.environ.get("LOGDNA_LOGHOST")
    SERVERNAME = os.environ.get("SERVERNAME")
    RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST")
    RABBITMQ_PORT = os.environ.get("RABBITMQ_PORT")
    RABBITMQ_USER = os.environ.get("RABBITMQ_USER")
    RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD")
    RABBITMQ_CERT_CRN = os.environ.get("RABBITMQ_CERT_CRN")
    RABBITMQ_QUEUE = os.environ.get("RABBITMQ_QUEUE")
    IAM_ENDPOINT = os.environ.get("IAM_ENDPOINT")
    CERT_MANAGER_ENDPOINT = os.environ.get("CERT_MANAGER_ENDPOINT")
    IBMCLOUD_APIKEY = os.environ.get("IBMCLOUD_APIKEY")
    