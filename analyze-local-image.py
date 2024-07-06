#!/usr/bin/env python3

import os
import sys
import glob
import logging
import requests
import config

# Logging configuration
logging.basicConfig(
    filename=config.logfile,
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%d-%m-%Y %H:%M:%S'
)

# Create a logger object
logger = logging.getLogger(__name__)

def get_image_path():
    """
    Determines the image path either from the command-line argument
    or by finding the latest image file in a specific directory.
    Returns the determined image path or None if no images found.
    """
    if len(sys.argv) >= 2:
        image_path = sys.argv[1]
        logger.info(f'Using passed argument for image path: {image_path}')
    else:
        directory_path = '/var/lib/motion/*-snapshot.jpg'
        list_of_files = glob.glob(directory_path)
        if list_of_files:
            image_path = max(list_of_files, key=os.path.getctime)
            logger.info(f'No argument found, using latest image: {image_path}')
        else:
            logger.error('No images found in the directory.')
            return None
    return image_path

def analyze_image(image_path):
    """
    Analyzes an image by sending it to a computer vision API and returns the analysis result.
    Parameters:
    - image_path: The path to the image file to be analyzed.
    Returns:
    - analysis: The JSON response from the computer vision API or None if an error occurs.
    """
    try:
        analyze_url = f"{config.computer_vision_endpoint}vision/v2.1/analyze"
        with open(image_path, 'rb') as image_data:
            headers = {
                'Ocp-Apim-Subscription-Key': config.computer_vision_subscription_key,
                'Content-Type': 'application/octet-stream'
            }
            params = {'visualFeatures': 'Tags,Faces,Objects,Description'}
            response = requests.post(analyze_url, headers=headers, params=params, data=image_data)
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f'Error sending request to Computer Vision API: {e}')
        return None

def parse_analysis_and_search(analysis):
    """
    Parses the analysis JSON to extract tags, objects, and description tags,
    and searches for predefined items within these categories.
    Parameters:
    - analysis: The JSON response from the computer vision API.
    Returns:
    - match: Boolean indicating whether any of the predefined items were found.
    """
    tag_list = [data['name'] for data in analysis.get('tags', [])]
    object_list = [data['object'] for data in analysis.get('objects', [])]
    description_list = analysis.get('description', {}).get('tags', [])

    tag_search = ['person', 'clothing']
    object_search = ['person', 'animal', 'mammal']
    description_search = ['man', 'standing', 'holding']

    tag_result = any(tag in tag_list for tag in tag_search)
    object_result = any(obj in object_list for obj in object_search)
    description_result = any(desc in description_list for desc in description_search)

    return tag_result or object_result or description_result

def send_telegram_message(message, image_path):
    """
    Sends a message and photo to Telegram.
    Parameters:
    - message: The text message to be sent.
    - image_path: The path to the image file to be sent.
    """
    telegram_url = f'https://api.telegram.org/bot{config.token}'
    send_message_url = f'{telegram_url}/sendMessage'
    send_photo_url = f'{telegram_url}/sendPhoto'

    try:
        tg_params = {'chat_id': config.chat_id, 'text': message}
        response = requests.post(send_message_url, params=tg_params)
        response.raise_for_status()
        logger.info('Message sent')

        with open(image_path, 'rb') as image_file:
            tg_image_data = {'photo': image_file}
            tg_params = {'chat_id': config.chat_id}
            response = requests.post(send_photo_url, params=tg_params, files=tg_image_data)
            response.raise_for_status()
        logger.info('Photo sent')
    except requests.exceptions.RequestException as e:
        logger.error(f'Error sending Telegram message: {e}')

def main():
    image_path = get_image_path()
    if not image_path:
        return

    analysis = analyze_image(image_path)
    if not analysis:
        return

    try:
        match = parse_analysis_and_search(analysis)

        if match:
            logger.info('Matching item found in analysis results.')
            send_telegram_message(config.message, image_path)
        else:
            logger.info('No matching item found in analysis results. No message sent.')
    except Exception as e:
        logger.error(f'Error occurred: {e}')

if __name__ == '__main__':
    main()
