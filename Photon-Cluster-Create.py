##############################################################################
# Platform:     Photon Controller 1.0RC1
# Description:  Cluster Creation Script
# Notes:        
# Log:          
##############################################################################
import requests
from requests.auth import HTTPDigestAuth
import json, menu

# Header formation for resftul Posts Puts, etc
headers = {'Content-Type': 'application/json'}

# Address to connect to the Controll instance or northbound NLB service
hostAddress = "10.63.251.31"
apiPort = '9000'

# Tenancy focus for location of cluster to be created
myTenant = input("Enter Tenant Name: ")

# Will add logic for user login later in case Lightwave enabled for authentication
# myResponse = requests.get(url,auth=HTTPDigestAuth(input("User Name: "), input("Password: ")), verify=True)

myResponse = requests.get('http://%s:%s/tenants?name=%s' % (hostAddress, apiPort, myTenant), verify=True)

if(myResponse.ok):
    print("Tenant Found")
    # Read the response to the deployment object
    resData = json.loads(myResponse.text)

    # Get the deployment ID to target the cluster creation
    tenantId = resData['items'][0]['id']

    myResponse = requests.get('http://%s:%s/tenants/%s/projects' % (hostAddress, apiPort, tenantid), verify=True)
    print(myResponse)
    #myProject = input("Enter Tenant Project: ")
     
else:
    myResponse.raise_for_status()