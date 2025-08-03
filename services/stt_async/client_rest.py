import argparse
import base64
import json
import os
import requests
import time
import uuid
from audio_converter import convert_audio

def print_diarization_output(finalized_diar_results):
    for segment in finalized_diar_results:
        print("\tfinal", segment["speaker_label"], ":", segment["transcript"])

    print("----")


def save_in_time_label_format(output_name, finalized_diar_results):
    with open(output_name + ".speakers", "w", encoding="utf-8") as out:
        for segment in finalized_diar_results:
            out.write(f"{int(segment['start_time_ms']) / 1000}\t{int(segment['end_time_ms']) / 1000}\t{segment['speaker_label']}\n")
    with open(output_name + ".text", "w", encoding="utf-8") as out:
        for segment in finalized_diar_results:
            out.write(f"{int(segment['start_time_ms']) / 1000}\t{int(segment['end_time_ms']) / 1000}\t{segment['transcript'].strip()}\n")


def run(args):
    base_url = "https://stt-async.x2agi.com:8444"
    converted_path = None
    converted_oracle_paths = []

    try:
        # Convert main audio if needed
        if not args.no_convert:
            print("Converting main audio to 16kHz mono WAV...")
            converted_path = convert_audio(args.path)
            audio_path = converted_path
        else:
            audio_path = args.path

        # Process oracle speakers
        oracle_speaker_labels = []
        if args.oracle_speakers:
            oracle_dir = os.path.dirname(os.path.abspath(args.oracle_speakers))
            
            with open(args.oracle_speakers, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    info = json.loads(line.strip())
                    
                    # Resolve relative path
                    original_audio_path = os.path.normpath(
                        os.path.join(oracle_dir, info["audio_filepath"])
                    )
                    
                    if not os.path.exists(original_audio_path):
                        raise FileNotFoundError(
                            f"Oracle audio not found: {original_audio_path} "
                            f"(line {line_num} in {args.oracle_speakers})"
                        )
                    
                    # Convert oracle audio if needed
                    if not args.no_convert:
                        print(f"Converting oracle audio: {original_audio_path}")
                        converted_oracle = convert_audio(original_audio_path)
                        converted_oracle_paths.append(converted_oracle)
                        audio_data_path = converted_oracle
                    else:
                        audio_data_path = original_audio_path

                    with open(audio_data_path, "rb") as audio_f:
                        audio_data = base64.b64encode(audio_f.read()).decode("utf-8")
                    
                    oracle_speaker_labels.append({
                        "speaker_label": info["speaker_label"],
                        "audio_data": audio_data
                    })

        # Read and encode main audio
        with open(audio_path, "rb") as audio_file:
            audio_content = base64.b64encode(audio_file.read()).decode("utf-8")

        # Setup request with retries
        retry_strategy = requests.adapters.Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
            backoff_jitter=0.3
        )
        
        with requests.Session() as session:
            adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            
            headers = {
                "Host": "stt-async.x2agi.com",
                "Authorization": f"Bearer {args.token}",
                "x-job-id": str(uuid.uuid4()),
                "x-language": args.lang,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # Initial recognition request
            payload = {
                "oracle_speaker_labels": oracle_speaker_labels,
                "restrict_to_oracle_speaker_labels": args.restrict_to_oracle_speaker_labels,
                "custom_options": "{}",
                "audio_data": audio_content
            }

            response = session.post(
                f"{base_url}/recognizeFileAsync",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Failed to start recognition: {response.status_code} - {response.text}")

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
                    raise RuntimeError("Recognition failed on server")

                time.sleep(2)

            # Get final results
            result_resp = session.get(
                f"{base_url}/getRecognition?operation_id={operation_id}",
                headers=headers,
                timeout=10
            )

            if result_resp.status_code != 200:
                raise RuntimeError(f"Failed to retrieve results: {result_resp.status_code}")

            finalized_diar_results = []
            for r in result_resp.json():
                for segment in r["results"]:
                    finalized_diar_results.append(segment)
            print_diarization_output(finalized_diar_results)

            if args.save:
                save_in_time_label_format(args.save, finalized_diar_results)

    finally:
        # Cleanup converted files
        if converted_path and os.path.exists(converted_path):
            os.remove(converted_path)
        for path in converted_oracle_paths:
            if os.path.exists(path):
                os.remove(path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", type=str, required=True, help="IAM token or API key")
    parser.add_argument("--lang", type=str, required=True, choices=["en", "ru"], 
                       help="Language of input audio")
    parser.add_argument("--path", type=str, default="example.wav", 
                       help="Audio file path")
    parser.add_argument("--restrict_to_oracle_speaker_labels", action="store_true", 
                       help="Restrict speakers to oracle labels")
    parser.add_argument("--oracle_speakers", type=str, default=None, 
                       help="JSONL file with speaker audio samples")
    parser.add_argument("--save", type=str, default=None, 
                       help="Base name for output files (.speakers and .text)")
    parser.add_argument("--no_convert", action="store_true", 
                       help="Skip audio conversion (files already 16kHz mono WAV)")

    args = parser.parse_args()
    run(args)
