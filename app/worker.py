import os, json, urllib, requests, fileinput, time, random, string
from subprocess import call, check_output, Popen
from datetime import datetime
from app import app
from random import seed, gauss

def getClusterRegionandResoureGroupName(reqid, cluster_name):
    app.logger.debug("{} - Getting cluster region and resource gruop for cluster {}".format(reqid, cluster_name))
    cluster_details = check_output(['ibmcloud', 'ks', 'cluster', 'get', '--cluster', cluster_name, '--json'])
    cluster_details_str = cluster_details.decode('utf8').replace("'",'"')
    cluster_details_dict = json.loads(cluster_details_str)
    region = cluster_details_dict['region']
    resourcegroupname = cluster_details_dict['resourceGroupName']
    app.logger.debug("{} Will return region={} and resource group name={}".format(reqid, region, resourcegroupname ))
    return region, resourcegroupname 

def getRabbitCert(reqid, apikey):
    app.logger.debug("{} Starting to get RabbitMQ Certificate ")
    iamToken = getiamtoken()
    certManagerEndpoint = app.config['CERT_MANAGER_ENDPOINT']
    header = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + iamToken["access_token"]
    }
    rabbit_crn = app.config['RABBITMQ_CERT_CRN']
    url = certManagerEndpoint+'/api/v2/certificate/'+urllib.parse.quote_plus(rabbit_crn)
    response = requests.get(url,headers=header)
    json_response = json.loads(response.text)
    
    return json_response['data']['content']

def getiamtoken():
    iamhost=os.environ.get("UTILITY_02CN_SERVICE_SERVICE_HOST")
    iamport=os.environ.get("UTILITY_02CN_SERVICE_SERVICE_PORT")
    iam_url="http://"+iamhost+":"+iamport+"/api/v1/getiamtoken/"
    iam_data = { "apikey":  app.config["IBMCLOUD_APIKEY"]}
    headers = { "Content-Type": "application/json" }
    resp = requests.get(iam_url, data=json.dumps(iam_data), headers=headers)
    iamtoken = resp.json()["iamtoken"]
    return iamtoken 

def enableSSHNode(reqid, apikey, cluster_name):
    app.logger.info("{} - Enabling SSH on Worker Nodes".format(reqid))
    try:
        call(['ibmcloud','login','--apikey', str(apikey), '--no-region', '-q'])
        call(['ibmcloud','ks','cluster','config','--cluster',str(cluster_name),'--admin'])

        region, resource_group_name = getClusterRegionandResoureGroupName(reqid, cluster_name)
            
        app.logger.debug("{} - Cluster Region = {} ".format(reqid, region))
        app.logger.debug("{} - Resource Group Name = {}".format(reqid, resource_group_name))
    
        cluster_details = check_output(['ibmcloud', 'ks', 'cluster', 'get', '--cluster', cluster_name, '--json'])
        cluster_details_str = cluster_details.decode('utf8').replace("'",'"')
        cluster_details_dict = json.loads(cluster_details_str)
        region = cluster_details_dict['region']
        app.logger.debug("{} region = {}".format(reqid, region))
        
        cluster_id = cluster_details_dict['id']
        app.logger.debug("{} cluster id = {}".format(reqid, cluster_id))
        
        resourceGroupId = cluster_details_dict['resourceGroup']
        app.logger.debug("{} resource group id = {}".format(reqid, resourceGroupId))
        
        worker_details = check_output(['ibmcloud', 'ks', 'workers', '--cluster', cluster_name, '--json'])
        worker_details_str = worker_details.decode('utf8').replace("'",'"')
        worker_details_dict = json.loads(worker_details_str)
        app.logger.debug("{} Here are the workers {}".format(reqid, worker_details_dict))
        # create and attach block to each worker node
        for worker in worker_details_dict:
            worker_id = worker["id"]
            # openshshift sees the worker_id as the ip address
            ocp_id = worker["networkInterfaces"][0]["ipAddress"]
            app.logger.debug("{} worker id = {}".format(reqid, worker_id))
            fin = open("/app/node-inspect-template.yaml", "rt")
            app.logger.debug("{} ocp id = {}".format(reqid, ocp_id))
            #read file contents to string
            data = fin.read()
            #replace all occurrences of the required string
            data = data.replace('WORKER-NODE-NAME', ocp_id)
            short_worker_id = worker_id[-40:]
            inspect_name = 'inspectnode-'+short_worker_id
            data = data.replace('inspectnode164121', inspect_name)
            #close the input file
            fin.close()
            
            fin = open("/app/"+worker_id+"-inspect-node.yaml", "wt")
            #overrite the input file with the resulting data
            fin.write(data)
            #close the file
            fin.close()

            #apply the yam
            call(['oc','apply','-f', '/app/'+worker_id+'-inspect-node.yaml','-n','kube-system'])
            
            # Delete the file after applying
            call(['rm','-rf','/app/'+worker_id+'-inspect-node.yaml'])
            app.logger.info("{} Successfully enabled ssh on worker node {}".format(reqid, worker_id))
            try:
                call(['/app/permitRootLogin.sh', inspect_name])
            except:
                # sometimes you have to try twice
                call(['/app/permitRootLogin.sh', inspect_name])
                pass
            
    except Exception as e:
        app.logger.error("{} - Error creating storage {}. {}".format(reqid, cluster_name, e))
    app.logger.info("{} Successfully completely enabling SSH on worker nodes".format(reqid))


def getresourcegroups(accountId, iamToken):
    # Get a list of current resource groups in accountId
    try:
        #accountId - getAccountId(apikey)
        headers = {"Authorization": "Bearer " + iamToken["access_token"]}   
        resp = requests.get(app.config['RESOURCE_CONTROLLER_ENDPOINT'] + '/v2/resource_groups?account_id=' + accountId,  headers=headers, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as errc:
        quit()
    except requests.exceptions.Timeout as errt:
        quit()
    except requests.exceptions.HTTPError as errb:
        if resp.status_code == 400:
            quit()
        elif resp.status_code == 401:
            quit()
        elif resp.status_code == 403:
            quit()

    if resp.status_code == 200:
        resourceGroups = json.loads(resp.content)["resources"]
    else:
        quit()

    return resourceGroups

def getresourcegroupid(reqid, resourceGroups, resourceGroupName):
    # search list for resource groups for resourceGroup and return ID
    resourceGroup = list(filter(lambda resourceGroup: resourceGroup['name'] == resourceGroupName, resourceGroups))
    app.logger.debug("resource group = {} for resource group name ".format(resourceGroup,resourceGroupName))
    if len(resourceGroup) > 0:
        resourceGroupId = resourceGroup[0]['id']
        app.logger.debug("{} Will return resource group id {}".format(reqid, resourceGroupId))
    else:
        resourceGroupId = None
        app.logger.error("{} Did not find resource group name {}".format(reqid, resourceGroupName))
  
    return resourceGroupId

def create_resource(reqid, auth_token, apiKey, cluster_name, region, resourcegroupid):
    
    try:
        app.logger.debug("{} - Starting create resource cluster name = {} region = {} resourcegroupid = {}".format(reqid, cluster_name, region, resourcegroupid))
        
        headers = {
            'Authorization': 'Bearer ' + str(auth_token),
            'Content-Type': 'application/json'
        }

        app.logger.debug("{} - Resource Plan Id = {}".format(reqid, app.config['RESOURCE_PLAN_ID']))
        
        data = {
            "name": "portworx_" + cluster_name,
            "target": "us-south",
            "resource_group": resourcegroupid,
            "resource_plan_id": app.config['RESOURCE_PLAN_ID'],
            "parameters": { "apikey": apiKey, "cluster_name": "portworxstoragecluster", "clusters": cluster_name, "internal_kvdb": "internal", "secret_type": "k8s" }
        }

        json_data = json.dumps(data)
        
        app.logger.debug("{} - creating resource {} with this data {}.".format(reqid, data["name"], data))
    
        response = requests.post('https://resource-controller.cloud.ibm.com/v2/resource_instances', headers=headers, data=json_data)
        response.raise_for_status()
        app.logger.debug("{} - Returned status code for creating the resource is {} ".format(reqid, response.status_code))
    except requests.exceptions.ConnectionError as errc:
        app.logger.debug("{} -Error Connecting: {}".format(reqid, errc))
    except requests.exceptions.Timeout as errt:
        app.logger.debug("{} -Timeout Error: {}".format(reqid, errt))
    except requests.exceptions.HTTPError as errb:
        if response.status_code == 400:
            app.logger.error("{} - The request could not be understood due to malformed syntax.".format(reqid))
            quit()
        elif response.status_code == 401:
            app.logger.error("{} - Your access token is invalid or authenication of your token failed.".format(reqid))
            quit()
        elif response.status_code == 403:
            app.logger.error("{} - Your access token is valid but does not have the necessary permissions to access this resource.".format(reqid))
            quit()
        elif response.status_code == 404:
            app.logger.error("{} - The resource could not be found.".format(reqid))
            quit()
        elif response.status_code == 429:
            app.logger.error("{} - too many requests. Please wait a few minutes and try again.".format(reqid))
            quit()
        elif response.status_code == 500:
            app.logger.error("{} - Your request could not be processed. Please try again later. If the problem persists, note the transaction-id in the response header and contact IBM Cloud support.".format(reqid))
            quit()
        if response.status_code == 201:
            app.logger.debug("{} - The resource {} was provisioned.".format(reqid, data["name"]))
        elif response.status_code == 202:
            app.logger.debug("{} - Request to provision the resource {} was accepted.".format(reqid, data["name"]))
        else:
            app.logger.error("{} - Unexpected result deleting creating resource {}.".format(reqid, data["name"]))
            
    return response

