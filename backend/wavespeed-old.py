import requests
import json
import time
import logging
_logger = logging.getLogger(__name__)

def generate_avatar(API_KEY, audio, image):

    url = "https://api.wavespeed.ai/api/v3/wavespeed-ai/infinitetalk-fast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "audio": audio,
        "image": image,
        "seed": -1
    }

    begin = time.time()
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        result = response.json()["data"]
        request_id = result["id"]
        _logger.error(f"Task submitted successfully. Request ID: {request_id}")
    else:
        _logger.error(f"Error: {response.status_code}, {response.text}")
        return

    url = f"https://api.wavespeed.ai/api/v3/predictions/{request_id}/result"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    # Poll for results
    final_url = ''
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()["data"]
            status = result["status"]

            if status == "completed":
                end = time.time()
                _logger.info(f"Task completed in {end - begin} seconds.")
                final_url = result["outputs"][0]
                _logger.error(f"Task completed. URL: {url}")
                break
            elif status == "failed":
                _logger.error(f"Task failed: {result.get('error')}")
                break
            else:
                _logger.info(f"Task still processing. Status: {status}")
        else:
            _logger.error(f"Error: {response.status_code}, {response.text}")
            break

        time.sleep(1)

    return final_url