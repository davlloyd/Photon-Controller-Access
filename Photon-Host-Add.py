##############################################################################
# Platform:     Photon Controller 1.0RC1
# Description:  Host Add Script
# Notes:        Written for Python 3.x   
# Log:          
##############################################################################
import requests
from requests.auth import HTTPDigestAuth
import json

# Header formation for resftul Posts Puts, etc
headers = {'Content-Type': 'application/json'}

# Address to connect to the Controll instance or northbound NLB service
hostAddress = "10.63.251.31"
apiPort = '9000'

# Will add logic for user login later in case Lightwave enabled for authentication
# myResponse = requests.get(url,auth=HTTPDigestAuth(input("User Name: "), input("Password: ")), verify=True)

myResponse = requests.get('http://%s:%s/deployments' % (hostAddress, apiPort), verify=True)

if(myResponse.ok):
    # Read the response to the deployment object
    resData = json.loads(myResponse.text)

    # Get the deployment ID to target the cluster creation
    deployId = resData['items'][0]['id']
    print(deployId)
     
    # Add hostAddress

    # Set Host to paused 
else:
    myResponse.raise_for_status()