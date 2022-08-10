#!/usr/bin/env python3

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
logging.basicConfig(
    filename=config.logfile,
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%d-%m-%Y %H:%M:%S')

# Get the filename from the argument passed from motion. If not specified use last file for testing
if len(sys.argv) >= 2:
    image_path = sys.argv[1]
    logging.info('Using passed argument for image path: ' + image_path)
else:
    #image_path = '/home/pi/computervision/44-20200417134311-19.jpg'
    list_of_files = glob.glob('/var/lib/motion/*-snapshot.jpg')
    image_path = max(list_of_files, key=os.path.getctime)
    logging.info('No argument found, using test image: ' + image_path)

# Read the image into a byte array and send to computer vision to confirm if person
analyze_url = config.computer_vision_endpoint + "vision/v2.1/analyze"
image_data = open(image_path, 'rb').read()
headers = {'Ocp-Apim-Subscription-Key': config.computer_vision_subscription_key,
           'Content-Type': 'application/octet-stream'}
params = {'visualFeatures': 'Tags,Faces,Objects,Description'}
response = requests.post(
    analyze_url, headers=headers, params=params, data=image_data)
response.raise_for_status()

# Output the full response to logs
analysis = response.json()
logging.info(analysis)

# Create a list of tags detected
tag_list = []
for data in analysis['tags']:
    result = data['name']
    tag_list.append(result)
logging.debug(tag_list)

# Output a friendly tag list to logs
logging.info("Tag List: {}".format(', '.join(map(str, tag_list))))

# Create a list of objects detected
object_list = []
for data in analysis['objects']:
    result = data['object']
    object_list.append(result)
logging.debug(object_list)

# Output a friendly object list to logs
logging.info("Object List: {}".format(', '.join(map(str, object_list))))

# Create a list of tags in the description detected
description_list = []
for data in analysis['description']['tags']:
    result = data
    description_list.append(result)
logging.debug(description_list)

# Output a friendly object list to logs
logging.info("Description List: {}".format(', '.join(map(str, description_list))))

# Define the items to show as a positive result
tag_search = ['person','clothing']
object_search = ['person', 'animal', 'mammal']
description_search = ['man', 'standing', 'holding']

# Search for the items in the results
tag_result = any(elem in tag_list for elem in tag_search)
object_result = any(elem in object_list for elem in object_search)
description_result = any(elem in description_list for elem in description_search)

# Search for match in results.
match = False

if tag_result:
    match = True
    logging.info('Matching tag found in List')
else:
    logging.info('No matching tag found')

if object_result:
    match = True
    logging.info('Matching object found in List')
else:
    logging.info('No matching object found')

# if description_result:
#    match = True
#    logging.info('Matching description found in List')
#else:
#    logging.info('No matching description found')
    
# Send message if results found
if match == True:
    # Construct the Telegram enpoint
    telegram_url = f'https://api.telegram.org/bot{config.token}'
    send_message_url = telegram_url + "/sendMessage"
    send_photo_url = telegram_url + "/sendPhoto"
    # Send message
    tg_params = {'chat_id': config.chat_id, 'text': config.message}
    response = requests.post(
    	send_message_url, params=tg_params)
    response.raise_for_status()
    logging.info('Message sent')
    # Send Photo
    tg_image_data = {'photo': open(image_path, 'rb')}
    tg_params = {'chat_id': config.chat_id}
    response = requests.post(
        send_photo_url, params=tg_params, files=tg_image_data)
    response.raise_for_status()
    logging.info('Photo sent')
else:
    logging.info('No message sent')