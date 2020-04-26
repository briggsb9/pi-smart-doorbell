# pi-smart-doorbell

A smart doorbell that takes a snapshot when motion is detected, and then confirms if the image contains a person before sending a message to your mobile. 

# Architecture
* The workflow is provided by a couple of python scripts set to run inside the motion detection software 'Motion'
* Azure Computer Vision provides the object detection to confirm a human presense
* A Telegram bot provides the messaging endpoint

![Image of components](https://github.com/SGGIRBS/pi-smart-doorbell/blob/master/images/smartcam.png)

# Prerequisites
* Raspberry Pi and power near your front door. Ether using the pi POE hat or the standard adaptor
* Raspberry Pi camera module with night vision and a long enough cable 
* Motion detection software for Linux. Motion https://github.com/Motion-Project
* Access to Azure. Sign up for a free Azure account here https://azure.microsoft.com/en-gb/free/
* Azure Cognitive Services Computer Vision endpoint and access key. Use this guide to create making sure you choose computer vision https://docs.microsoft.com/en-us/azure/cognitive-services/cognitive-services-apis-create-account?tabs=multiservice%2Clinux
* Telegram App installed registered on your mobile device https://telegram.org/apps
* Telegram bot. Create using this guide https://core.telegram.org/bots#6-botfather
* Telegram group with the bot added

TBC
