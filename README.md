# pi-smart-doorbell

A smart doorbell that takes a snapshot when motion is detected, and then confirms if the image contains a person before sending a message to your mobile. 

# Architecture
* Azure Computer Vision provides the object detection to confirm a human presense
* A Telegram bot provides the messaging endpoint
* Two custom python scripts are triggered inside the motion detection software 'Motion'. The first takes a snapshot when motion is detected in the center of the cameras FOV. The second handles the API calls to Azure and Telegram

![Image of components](https://github.com/SGGIRBS/pi-smart-doorbell/blob/master/images/smartcam.png)

# Example Telegram Notification

![Example message](https://github.com/SGGIRBS/pi-smart-doorbell/blob/master/images/example-message-small2.png)

# Prerequisites
* Raspberry Pi and power near your front door. Ether using the pi POE hat or the standard power adaptor
* Raspberry Pi camera module with night vision and a long enough cable 
* Motion detection software for Linux. Motion https://github.com/Motion-Project
* Access to Azure. Sign up for a free Azure account here https://azure.microsoft.com/en-gb/free/
* Azure Cognitive Services Computer Vision endpoint and access key
* Telegram App installed registered on your mobile device https://telegram.org/apps
* Telegram bot. Create using this guide https://core.telegram.org/bots#6-botfather
* Telegram group with the bot added

