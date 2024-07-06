#!/usr/bin/env python3

import os
import sys
import glob
import logging
import requests
import config
from requests.adapters import HTTPAdapter, Retry
from azure.storage.blob import BlobServiceClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

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
    Analyzes an image by sending it to the Computer Vision API using the Azure SDK and returns the analysis result.
    Parameters:
    - image_path: The path to the image file to be analyzed.
    Returns:
    - analysis: The JSON response from the computer vision API or None if an error occurs.
    """
    try:
        # Authenticate with the Computer Vision service
        credentials = CognitiveServicesCredentials(config.computer_vision_subscription_key)
        client = ComputerVisionClient(config.computer_vision_endpoint, credentials)
        # Specify the features to be retrieved
        visual_features = ["Tags", "Faces", "Objects", "Description"]
        # Open the image file
        with open(image_path, "rb") as image_data:
            # Analyze the image
            analysis = client.analyze_image_in_stream(image_data, visual_features=visual_features)
        # Log tags
        if analysis.tags:
            tag_names = [tag.name for tag in analysis.tags]
            logger.info(f"Tags: {tag_names}")

        # Log description captions and tags
        if analysis.description:
            captions = [caption.text for caption in analysis.description.captions]
            description_tags = analysis.description.tags
            logger.info(f"Description Captions: {captions}")
            logger.info(f"Description Tags: {description_tags}")

        # Log detected objects
        if analysis.objects:
            objects_info = [{"object": obj.object_property, "confidence": obj.confidence} for obj in analysis.objects]
            logger.info(f"Objects: {objects_info}")
        return analysis
    except FileNotFoundError as e:
        logger.error(f'Image file not found: {image_path}. Error: {e}')
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f'Network error occurred while sending request to Computer Vision API: {e}')
        return None
    except Exception as e:
        logger.error(f'Unexpected error sending request to Computer Vision API: {e}')
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
    tag_list = [tag.name for tag in analysis.tags]
    object_list = [obj.object_property for obj in analysis.objects]
    description_list = analysis.description.tags

    # Output a friendly list to logs for easier debugging
    logger.info("Tag List: {}".format(', '.join(tag_list)))
    logger.info("Object List: {}".format(', '.join(object_list)))
    logger.info("Description List: {}".format(', '.join(description_list)))

    tag_search = ['person', 'clothing']
    object_search = ['person', 'animal', 'mammal']
    description_search = ['man', 'standing', 'holding']

    tag_result = any(tag in tag_list for tag in tag_search)
    object_result = any(obj in object_list for obj in object_search)
    description_result = any(desc in description_list for desc in description_search)

    return tag_result or object_result or description_result

def send_telegram_message(message, image_path):
    """
    Sends a message and photo to Telegram with retry logic for HTTPS requests.
    Parameters:
    - message: The text message to be sent.
    - image_path: The path to the image file to be sent.
    """
    telegram_url = f'https://api.telegram.org/bot{config.token}'
    send_message_url = f'{telegram_url}/sendMessage'
    send_photo_url = f'{telegram_url}/sendPhoto'

    # Configure retry strategy for HTTPS requests
    retry_strategy = Retry(
        total=3,  # Total number of retries
        status_forcelist=[502, 503, 504],  # Status codes to retry
        allowed_methods=["POST"],  # HTTP methods to retry
        backoff_factor=1  # Backoff factor to apply between attempts
    )

    # Create a session and mount the HTTPAdapter for HTTPS
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('https://', adapter)

    try:
        tg_params = {'chat_id': config.chat_id, 'text': message}
        response = session.post(send_message_url, params=tg_params)
        response.raise_for_status()
        logger.info('Message sent')

        with open(image_path, 'rb') as image_file:
            tg_image_data = {'photo': image_file}
            response = session.post(send_photo_url, params={'chat_id': config.chat_id}, files=tg_image_data)
            response.raise_for_status()
        logger.info('Photo sent')
    except requests.exceptions.RequestException as e:
        logger.error(f'Error sending Telegram message: {e}')
    finally:
        session.close()

def upload_to_blob_storage(file_path):
    """
    Uploads a file to Azure Blob Storage using a SAS token for authentication.
    All necessary information is pulled from a configuration file.
    Parameters:
    - file_path: The path to the file to be uploaded.
    """
    try:
        # Construct the BlobServiceClient with a SAS URL
        blob_service_client = BlobServiceClient(account_url=f"https://{config.storage_account_name}.blob.core.windows.net?{config.sas_token}")
        
        # Get a client to interact with the specified container
        container_client = blob_service_client.get_container_client(config.container_name)
        
        # Get a client to interact with the specified blob (file)
        blob_client = container_client.get_blob_client(os.path.basename(file_path))
        
        # Open the file and upload its contents to Azure Blob Storage
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data)
        
        logger.info(f"Uploaded {file_path} to Azure Blob")
    
    except Exception as e:
        logger.error(f"Error uploading to Azure Blob Storage: {e}")

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
            upload_to_blob_storage(image_path)
        else:
            logger.info('No matching item found in analysis results. No message sent.')
    except Exception as e:
        logger.error(f'Error occurred: {e}')

if __name__ == '__main__':
    main()
