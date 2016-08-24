##############################################################################
# Platform:     Photon Controller 1.0RC1
# Description:  Cluster Creation Script
# Notes:        
# Log:          
##############################################################################
import requests
from requests.auth import HTTPDigestAuth
import json

#Address to connect to the Controll instance or northbound NLB service
url = "http://10.63.251.31:9000/deployments"

# Tenancy focus for location of cluster to be created
myTenant = raw_input("Enter Tenant Name: ")
myProject = raw_input("Enter Tenant Project: ")

# Will add logic for user login later in case Lightwave enabled for authentication
# myResponse = requests.get(url,auth=HTTPDigestAuth(raw_input("User Name: "), raw_input("Password: ")), verify=True)

myResponse = requests.get(url, verify=True)

if(myResponse.ok):

    jData = json.loads(myResponse.content)

    print("The response contains {0} properties".format(len(jData)))
    print("\n")
    for key in jData:
        print(key + " : " + jData[key])
else:
    myResponse.raise_for_status()