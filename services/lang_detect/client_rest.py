import argparse
import base64
import os
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Import conversion function (can be commented out)
from audio_converter import convert_audio

# ==============================
# Request Handling Module
# ==============================
def make_api_request(url: str, headers: dict, payload: dict) -> requests.Response:
    """Make API request with retry logic"""
    # Configure retry strategy
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,    # Base delay of 2 seconds
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"],
        raise_on_status=False,
        backoff_jitter=0.3   # 30% jitter variation
    )
    
    with requests.Session() as session:
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        
        try:
            response = session.post(
                url,
                headers=headers,
                json=payload,
                timeout=4
            )
            return response
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request failed after retries: {str(e)}")

# ==============================
# Main Function
# ==============================
def run(args):
    # API configuration
    url = "https://lang-detect.x2agi.com:8444/detectFromAudio"
    headers = {
        "Host": "lang-detect.x2agi.com",
        "Authorization": f"Bearer {args.token}",
        "Content-Type": "application/json",
    }

    converted_path = None
    try:
        # Audio processing
        if args.no_convert:
            print("Skipping audio conversion")
            audio_path = args.path
        else:
            print("Converting audio to 16kHz mono WAV...")
            converted_path = convert_audio(args.path)
            audio_path = converted_path

        # Read audio data
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        with open(audio_path, "rb") as audio_file:
            audio_content = base64.b64encode(
                audio_file.read(4 * 1024 * 1024)  # Read up to 4MB
            ).decode("utf-8")

        # Prepare payload
        payload = {
            "audio_data": audio_content,
            "allowed_languages": args.allowed_languages.split(",") if args.allowed_languages else []
        }

        # Make API request
        print("Sending request...")
        response = make_api_request(url, headers, payload)
        
        # Handle response
        if 200 <= response.status_code < 300:
            print("Success:")
            print(f"response={response.json()}")
        else:
            print(f"Failed ({response.status_code}): {response.text}")
            
    finally:
        # Clean up temporary file
        if converted_path and os.path.exists(converted_path):
            os.remove(converted_path)

# ==============================
# CLI Interface
# ==============================
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", type=str, required=True, help="API key")
    parser.add_argument("--path", type=str, default="example.wav", help="Audio file path")
    parser.add_argument("--allowed_languages", type=str, default=None, 
                      help="Comma-separated list of allowed languages (e.g., 'en,ru')")
    parser.add_argument("--no_convert", action="store_true", 
                      help="Skip audio conversion (use if file is already 16kHz mono WAV)")
    args = parser.parse_args()
    
    run(args)
