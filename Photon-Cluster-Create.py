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

# General cluster variables
clusterFile = 'mesosclustertemplate.json'
clusterName = 'notthename'

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
    global hostAddress, apiPort, clusterFile, clusterName

    if os.path.isfile(clusterFile):
        clusterTemplate = open(clusterFile, 'r')
        content = clusterTemplate.read()
        clusterTemplate.close()

        clusterName = input("\nEnter Cluster Name: ")

        content = content.replace('<NAME>', clusterName)
        content = content.replace('<NETWORKID>', getNetworkId())
        content = content.replace('<ZOO1>', input("\nEnter Zookeeper IPAddress: "))
        content = content.replace('<NETMASK>', "255.255.255.0")
        content = content.replace('<GATEWAY>', "10.63.251.1")

        print("\nCluster Creation Starting")    
        aResponse = requests.post('http://%s:%s/projects/%s/clusters' % (hostAddress, apiPort, projectId), json=json.loads(content))
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
# Only need the project id sent through as cluster name is set as global value 
def clusterConsoleIp(projectId):
    global hostAddress, apiPort
    global clusterName

    # Get all the networks
    myResponse = requests.get('http://%s:%s/projects/%s/clusters' % (hostAddress, apiPort, projectId), verify=True)
    
    #make sure it responded well
    if(myResponse.ok):
        # get the clusters listed
        for clusterItem in json.loads(myResponse.text)['items']:
            if(clusterItem['name'] == clusterName):
                clusterId = clusterItem['id']
                break
        
        if(clusterId):
            clusterVMs = requests.get('http://%s:%s/clusters/%s/vms' % (hostAddress, apiPort, clusterId), verify=True)
            if(clusterVMs.ok):
                # Getting the VMs from the cluster and looking for the VM with the Marathon role
                for vmItem in json.loads(clusterVMs.text)['items']:
                    if(vmItem['name'].upper().startswith("MARATHON")):
                        vmIp = getVMIP(vmItem['id'])
                        return vmIp
            else:
                print("Failed to get VM list from cluster %s" % clusterName)
                return None
        else:
            print("Did not find cluster %s" % clusterName)
            return None
    else:
        print('Reponse from Photon failed')
        return None

# Get tghe IP address of a vm
def getVMIP(vmId):
    global hostAddress, apiPort

    # Get all the networks associated to a vm, this creates a task to collect the address details from the 
    # vm. The VM Network object will return task identifier which collects the details
    resData = requests.get('http://%s:%s/vms/%s/networks' % (hostAddress, apiPort, vmId), verify=True)
        
    #make sure it responded well
    if(resData.ok):
        try:
            # Now need to get the task id as the network data is reported within the task as it is a point in 
            # time value due to DHCP so is not stored with the vm
            taskId = json.loads(resData.text)['id']
            resData = requests.get('http://%s:%s/tasks/%s' % (hostAddress, apiPort, taskId), verify=True)
            # Reading the network interface to find one with an id. The private container has a null id
            # Of course this might change
            for netConn in json.loads(resData.text)['resourceProperties']['networkConnections']:
                if netConn['network']:
                    ipAddress = netConn['ipAddress']

            return ipAddress
        except:
            print("Failed getting task")
            return None
    

# Wait for tasks to complete
def taskWait(taskId):
    global hostAddress, apiPort

    print("\nTracking Task: -", end='')
    counter = 0
    while True:
        counter += 1
        # Get the task details
        aResponse = requests.get('http://%s:%s/tasks/%s' % (hostAddress, apiPort, taskId), verify=True)
        
        #make sure it responded well
        if(aResponse.ok):
            if counter % 2 == 0:
                print('\b|', end='')
            else:
                print('\b-', end='')

            resData = json.loads(aResponse.text)
            try:
                taskState = resData['state']
                if taskState == "COMPLETED":
                    return True
                elif taskState == "ERROR":
                    print("\nTask did not complete successfully")
                    return None

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
        # Get the cluster UI address
        clusterConsoleIp = clusterConsoleIp(projectId)
        if (clusterConsoleIp):
            print('\nCluster %s Created, browse to http://%s:8080 to access Marathon' % (clusterName, clusterConsoleIp))
        else:
            print('\nOops... something didn''t work getting the cluster details!')
    else:
        print("\nSomething happened waiting for the task to complete") 
else:
    print("\nTenant not found")
