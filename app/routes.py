import json, pika, ssl, random, subprocess
from app import app
from app.worker import *


app.logger.info('Connecting to queue')
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
context.verify_mode = ssl.CERT_REQUIRED
context.load_verify_locations('rabbit-crt.pem')
conn_params = pika.ConnectionParameters(port=app.config['RABBITMQ_PORT'],
                                        host=app.config['RABBITMQ_HOST'],
                                        credentials=pika.PlainCredentials(app.config['RABBITMQ_USER'],
                                                        app.config['RABBITMQ_PASSWORD']),
                                        ssl_options=pika.SSLOptions(context),
                                        heartbeat=3000,  
                                        blocked_connection_timeout=300)

connection = pika.BlockingConnection(conn_params)
channel = connection.channel()

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

@app.shell_context_processor
def waitformessage():
    channel.basic_consume(app.config['RABBITMQ_QUEUE'], callback, auto_ack=True)
    app.logger.info('Waiting for actions to be received...')
    channel.start_consuming()
    
def enableSSH(message):
    reqid = message["reqid"]
    apikey = message["APIKEY"]
    cluster_name = message["CLUSTER_NAME"]
    enableSSHNode(reqid, apikey, cluster_name)

def callback(ch, method, properties, body):
    raw_message = json.loads(body)
    message = json.loads(raw_message)
    reqid = randomString()
    app.logger.debug("Received message {} ID = {}".format(message, reqid))
    
    if message["action"] == "enableSSH":
        app.logger.info("Received request to enable SSH")
        enableSSH(message)
    else:
        app.logger.info("Received unknown request {}".format(message))
