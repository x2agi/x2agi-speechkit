import argparse
import requests
import uuid
import time
import json
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def run(args):
    base_url = "https://postprocess-asr.x2agi.ru:8444" 

    # Configure retry strategy
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST", "GET"],
        raise_on_status=False,
        backoff_jitter=0.3
    )

    with requests.Session() as session:
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://",  adapter)

        job_id = str(uuid.uuid4())  # job id is used for routing, need to regenerate WITHIN retry loop - otherwise the request will go to the same failing endpoint

        headers = {
            "Host": "postprocess-asr.x2agi.ru",
            "Authorization": f"Bearer {args.token}",
            "x-job-id": job_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Read input files
        with open(args.input_speakers, "r", encoding="utf-8") as f:
            speakers_content = f.read()
        with open(args.input_text, "r", encoding="utf-8") as f:
            utterances_content = f.read()

        # Validate language
        if args.lang not in ["en", "ru"]:
            raise ValueError(f"Invalid language: {args.lang}. Must be 'en' or 'ru'")

        # Prepare request payload
        payload = {
            "speakers": speakers_content,
            "utterances": utterances_content,
            "min_pause_to_separate": args.min_pause_to_separate,
            "as_monologue": args.as_monologue,
            "language": args.lang
        }

        # Initial processing request
        response = session.post(
            f"{base_url}/postprocessAsrAsync",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Failed to start processing: {response.status_code} - {response.text}")

        operation_id = response.json().get("id")
        print(f"Server returned operation ID = {operation_id}")

        # Polling loop
        while True:
            progress_resp = session.get(
                f"{base_url}/getProgress?operation_id={operation_id}",
                headers=headers,
                timeout=10
            )
            
            if progress_resp.status_code != 200:
                raise RuntimeError(f"Progress check failed: {progress_resp.status_code}")
            
            progress_data = progress_resp.json()
            print(f"Progress: {progress_data['progress']}%, Status: {progress_data['status']}")

            if progress_data["status"] == "completed":
                break
            elif progress_data["status"] == "failed":
                raise RuntimeError("Processing failed on server")

            time.sleep(2)

        # Get final results
        result_resp = session.get(
            f"{base_url}/getRecognition?operation_id={operation_id}",
            headers=headers,
            timeout=10
        )

        if result_resp.status_code != 200:
            raise RuntimeError(f"Failed to retrieve results: {result_resp.status_code}")

        result_data = result_resp.json()
        print(f"response.speakers={result_data['speakers']}")
        print(f"response.text={result_data['utterances']}")

        # Save outputs
        with open(args.output_speakers, "w", encoding="utf-8") as f:
            f.write(result_data["speakers"] + "\n")
        with open(args.output_text, "w", encoding="utf-8") as f:
            f.write(result_data["utterances"] + "\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", type=str, required=True, help="IAM token or API key")
    parser.add_argument("--lang", type=str, required=True, choices=["en", "ru"], 
                       help="Language of input text")
    parser.add_argument("--input_speakers", type=str, required=True, 
                       help="Input file with timestamps and speaker labels")
    parser.add_argument("--input_text", type=str, required=True, 
                       help="Input file with timestamps and utterances")
    parser.add_argument("--output_speakers", type=str, required=True, 
                       help="Output file for processed speaker labels")
    parser.add_argument("--output_text", type=str, required=True, 
                       help="Output file for processed utterances")
    parser.add_argument("--min_pause_to_separate", type=float, default=5.0, 
                       help="Minimum pause (sec) to keep utterances separate (default: 5.0)")
    parser.add_argument("--as_monologue", action="store_true", 
                       help="Force single speaker mode")

    args = parser.parse_args()
    run(args)
