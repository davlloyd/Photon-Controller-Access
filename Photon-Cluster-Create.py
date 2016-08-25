##############################################################################
# Platform:     Photon Controller 1.0RC1
# Description:  Cluster Creation Script
# Notes:        Python3
#               Will add logic for user login later in case Lightwave enabled for authentication
#
# Log:          First cut restricted to Mesos, others easy to add 
##############################################################################
import requests
from requests.auth import HTTPDigestAuth
import json, os, time

# Header formation for resftul Posts Puts, etc
headers = {'Content-Type': 'application/json'}

# Address to connect to the Controll instance or northbound NLB service
hostAddress = "10.63.251.31"
apiPort = '9000'
clusterFile = 'mesosclustertemplate.json'

# Get the Id for the Tenant specified by the user
def getTenantID():
    global hostAddress, apiPort

    # Tenancy focus for location of cluster to be created
    myTenant = input("\n\nEnter Tenant Name: ")
    # Get Tenant Details
    myResponse = requests.get('http://%s:%s/tenants?name=%s' % (hostAddress, apiPort, myTenant), verify=True)

    if(myResponse.ok):
        # Read the response to the deployment object
        resData = json.loads(myResponse.text)

        try:
            # Get the deployment ID to target the cluster creation
            tenantId = resData['items'][0]['id']
            return tenantId
        except:
            return None

    else:
        return None

# Get the project Id from the tenant selected
def getProjectID(tenantId):
    global hostAddress, apiPort    

    # Get the project list for the tenant
    myResponse = requests.get('http://%s:%s/tenants/%s/projects' % (hostAddress, apiPort, tenantId), verify=True)

    #make sure it responded well
    if(myResponse.ok):
        items = 0
        myProjects = dict()
        
        # List out the projects so that the correct one can be selected
        print("Select Target Project:\n")
        for projectItem in json.loads(myResponse.text)['items']:
            items += 1
            myProjects[items] = projectItem['id']
            print('%i:  %s' % (items, projectItem['name']))

        print('\nSelect Project (1 - %i)' % items)
        while True:
            try:
                userResponse = int(input())
                if userResponse < 1 or userResponse > items:
                    print ('Wrong, try again!')
                else:
                    break
            except ValueError:
                print('It does need to be a number!')
        
        return myProjects[userResponse]
    else:
        return None

# get the network id

# Create the cluster into the select project
def createCluster(projectId):
    global hostAddress, apiPort, clusterFile

    if os.path.isfile(clusterFile):
        clusterTemplate = open(clusterFile, 'r')
        content = clusterTemplate.read()
        clusterTemplate.close()

        content = content.replace('<NAME>', input("\nEnter Cluster Name: "))
        content = content.replace('<NETWORKID>', getNetworkId())
        content = content.replace('<ZOO1>', input("\nEnter Zookeeper IPAddress: "))
        content = content.replace('<NETMASK>', "255.255.255.0")
        content = content.replace('<GATEWAY>', "10.63.251.1")
    
        aResponse = requests.post('http://%s:%s/projects/%s/clusters' % (hostAddress, apiPort, projectId), json=json.loads(content), verify=True)
        if(aResponse.ok):
            resData = json.loads(aResponse.text)
            try:
                taskId = resData['id']
                print("\nCluster Creation Commenced: %s" % taskId)
                return taskId
            except:
                print("\nGetting Cluster Create taskId failed")
                return None
        else:
            print("\nCluster Creation Failed: %s" % aResponse)
            return None

    else:
        print('\nCan not find file %s' % clusterFile)
        return None

# Get the networkid of the default network
def getNetworkId():
    global hostAddress, apiPort

    # Get all the networks
    myResponse = requests.get('http://%s:%s/subnets' % (hostAddress, apiPort), verify=True)
    
    #make sure it responded well
    if(myResponse.ok):
        
        # get the subnets listed
        for netItem in json.loads(myResponse.text)['items']:
            if(netItem['isDefault']):
                return netItem['id']
                break

        print("Did not find default network")
    else:
        print("Did not get back list of subnets")

    
# Get the UI IP address for cluster
def clusterConsoleIp(clusterId):
    return None

# Wait for tasks to complete
def taskWait(taskId):
    global hostAddress, apiPort

    print("Tracking Task: ")
    while True:
        # Get the task details
        aResponse = requests.get('http://%s:%s/tasks/%s' % (hostAddress, apiPort, taskId), verify=True)
        
        #make sure it responded well
        if(aResponse.ok):
            resData = json.loads(aResponse.text)
            try:
                taskState = resData['state']
                if taskState == "COMPLETED":
                    return True
                elif taskState == "ERROR":
                    print("Task did not complete successfully")
                    return None
                print("\r.")
                time.sleep(5)
            except:
                print("\nTask status tracking failed")
                return None
        else:
            print("\nCluster Creation Failed: %s" % aResponse)
            return None


# Lets get going
tenantId = getTenantID()
if(tenantId):
    projectId = getProjectID(tenantId)
    taskId = createCluster(projectId)
    if(taskWait(taskId)):
        clusterId = clusterConsoleIp()
        if (clusterId):
            print('Cluster Created, browse to http://%s to access Marathon' % clusterId)
        else:
            print('Oops... something didn''t work!')   
else:
    print("Tenant not found")
