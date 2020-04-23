import config
import os
import json
import sys
import requests
import glob
import logging
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

# Logging config
#logging.basicConfig(filename='pi-smart-doorbell.log',level=logging.DEBUG)

# Get the filename from the argument passed from motion. If not specified use last file for testing
if len(sys.argv) >= 2:
    image_path = sys.argv[1]
    #logging.info('Using passed argument for image path' + image_path)
else:
    #image_path = '/home/pi/computervision/44-20200417134311-19.jpg'
    list_of_files = glob.glob('/var/lib/motion/*-snapshot.jpg')
    image_path = max(list_of_files, key=os.path.getctime)
    #logging.info('No argument found, using test image' + image_path)

# Read the image into a byte array and send to computer vision to confirm if person
analyze_url = computer_vision_endpoint + "vision/v2.1/analyze"
image_data = open(image_path, 'rb').read()
headers = {'Ocp-Apim-Subscription-Key': computer_vision_subscription_key,
           'Content-Type': 'application/octet-stream'}
params = {'visualFeatures': 'Tags,Faces,Objects'}
response = requests.post(
    analyze_url, headers=headers, params=params, data=image_data)
response.raise_for_status()

# Output the response
analysis = response.json()
print(analysis)
#logging.info(analysis)

# Check results for people
object_list = []
for data in analysis['objects']:
    result = data['object']
    object_list.append(result)

# Construct the Telegram enpoint
telegram_url = f'https://api.telegram.org/bot{token}'
send_message_url = telegram_url + "/sendMessage"
send_photo_url = telegram_url + "/sendPhoto"

if object_list == ['person'] or object_list == ['animal'] or object_list == ['mammal']:
    print("Matching object found in List : " , object_list)
    # Send message
    tg_params = {'chat_id': chat_id, 'text': message}
    response = requests.post(
    	send_message_url, params=tg_params)
    response.raise_for_status()
    # Send Photo
    tg_image_data = {'photo': open(image_path, 'rb')}
    tg_params = {'chat_id': chat_id}
    response = requests.post(
        send_photo_url, params=tg_params, files=tg_image_data)
    response.raise_for_status()
