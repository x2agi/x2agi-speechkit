import argparse
import grpc
import json
import os
import time
import uuid
import stt_async.stt_async_service_pb2
import stt_async.stt_async_service_pb2_grpc
import yandex.cloud.operation.operation_pb2 as operation_pb2

from audio_converter import convert_audio

CHUNK_SIZE = 1024 * 1024  # 1MB chunks (adjust based on your needs)

def print_diarization_output(finalized_diar_results):
    for segment in finalized_diar_results:
        print("\tfinal", segment.speaker_label, ":", segment.transcript)

    print("----")


def save_in_time_label_format(output_name, finalized_diar_results):
    with open(output_name + ".speakers", "w", encoding="utf-8") as out:
        for segment in finalized_diar_results:
            out.write(f"{segment.start_time_ms / 1000}\t{segment.end_time_ms / 1000}\t{segment.speaker_label}\n")
    with open(output_name + ".text", "w", encoding="utf-8") as out:
        for segment in finalized_diar_results:
            out.write(f"{segment.start_time_ms / 1000}\t{segment.end_time_ms / 1000}\t{segment.transcript.strip()}\n")


def generate_requests(args, oracle_speaker_labels, audio_path):
    # First request: Contains session options
    yield stt_async.stt_async_service_pb2.RecognizeFileStreamingRequest(
        options=stt_async.stt_async_service_pb2.RecognitionOptions(
            oracle_speaker_labels=oracle_speaker_labels,
            restrict_to_oracle_speaker_labels=args.restrict_to_oracle_speaker_labels,
            custom_options="{}",
        )
    )

    # Subsequent requests: Stream audio chunks
    with open(audio_path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            yield stt_async.stt_async_service_pb2.RecognizeFileStreamingRequest(audio_data=chunk)


def run(args):
    if args.lang not in ["en", "ru"]:
        raise ValueError(f"expected --lang: 'en' or 'ru', got '{args.lang}'")

    converted_path = None
    converted_oracle_paths = []  # Track converted oracle files

    try:
        # Convert main audio file if needed
        if args.no_convert:
            print("Skipping audio conversion for main file")
            audio_path = args.path
        else:
            print("Converting main audio to 16kHz mono WAV...")
            converted_path = convert_audio(args.path)
            audio_path = converted_path

        # Process oracle speakers
        oracle_speaker_labels = []
        if args.oracle_speakers is not None:
            oracle_dir = os.path.dirname(os.path.abspath(args.oracle_speakers))
            assert os.path.exists(args.oracle_speakers), f"Cannot find {args.oracle_speakers}"
            with open(args.oracle_speakers, "r", encoding="utf-8") as inp:
                for line_num, line in enumerate(inp, 1):
                    try:
                        info = json.loads(line.strip())
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON in line {line_num} of {args.oracle_speakers}")

                    # Resolve relative paths to oracle_speakers directory
                    original_audio_path = os.path.normpath(
                        os.path.join(oracle_dir, info["audio_filepath"])
                    )

                    if not os.path.exists(original_audio_path):
                        raise FileNotFoundError(
                            f"Oracle audio file not found: {original_audio_path} "
                            f"(from line {line_num} in {args.oracle_speakers})"
                        )
                    
                    # Convert oracle audio if needed
                    if not args.no_convert:
                        print(f"Converting oracle audio: {original_audio_path}")
                        converted_oracle = convert_audio(original_audio_path)
                        converted_oracle_paths.append(converted_oracle)
                        audio_data_path = converted_oracle
                    else:
                        audio_data_path = original_audio_path

                    with open(audio_data_path, "rb") as f:
                        data = f.read()
                    oracle_speaker_labels.append(
                        stt_async.stt_async_service_pb2.OracleSpeakerLabel(
                            audio_data=data,
                            speaker_label=info["speaker_label"]
                        )
                    )
        print(f"len(oracle_speaker_labels)={len(oracle_speaker_labels)}")

        # Generate job_id on the client before any requests
        job_id = str(uuid.uuid4())

        # Установите соединение с сервером.
        with grpc.secure_channel(
            "stt-async.x2agi.com:8443",
            grpc.ssl_channel_credentials(),
            options=[
                ("grpc.ssl_target_name_override", "stt-async.x2agi.com"),  # Force SNI
                ("grpc.default_authority", "stt-async.x2agi.com"),
                # Recommended optimizations:
                ("grpc.keepalive_time_ms", 10000),
                ("grpc.max_receive_message_length", 50 * 1024 * 1024)
            ]
        ) as channel:

            stub = stt_async.stt_async_service_pb2_grpc.AsyncRecognizerStub(channel)

            initial_metadata = [
                ("authorization", f"Bearer {args.token}"),
                ("x-job-id", job_id),
                ("x-language", args.lang),
            ]

            # Stream the requests to the server
            operation = stub.RecognizeFileStreaming(
                generate_requests(args, oracle_speaker_labels, audio_path),
                metadata=initial_metadata
            )

            # operation.id is returned by the server, but routing is pinned by x-job-id
            print(f"server returned operation ID = {operation.id}")

            # Poll the progress until the status is "completed"
            while True:
                get_progress_request = stt_async.stt_async_service_pb2.GetProgressRequest(operation_id=operation.id)
                progress_response = stub.GetProgress(get_progress_request, metadata=initial_metadata)

                status, progress = progress_response.status, progress_response.progress
                print(f"Progress: {progress}%, Status: {status}")

                if status == "completed":
                    break  # Exit the loop when the operation is completed
                elif status == "failed":
                    raise RuntimeError("Recognition operation failed: please contact support.")

                time.sleep(5)  # Wait before polling again

            # Call GetRecognition
            get_recognition_request = stt_async.stt_async_service_pb2.GetRecognitionRequest(operation_id=operation.id)
            responses = stub.GetRecognition(get_recognition_request, metadata=initial_metadata)

            finalized_diar_results = []  # list of tuples (speaker_label, text)
            for r in responses:
                for segment in r.results:
                    finalized_diar_results.append(segment)
            print_diarization_output(finalized_diar_results)
            if args.save:
                save_in_time_label_format(args.save, finalized_diar_results)

    finally:
        if converted_path and os.path.exists(converted_path):
            os.remove(converted_path)
        for path in converted_oracle_paths:
            if os.path.exists(path):
                os.remove(path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", type=str, required=True, help="IAM token or API key")
    parser.add_argument("--lang", type=str, required=True, help="Language of input text: ['ru', 'en']")
    parser.add_argument("--path", type=str, default="example.wav", help="audio file path")
    parser.add_argument("--restrict_to_oracle_speaker_labels", action="store_true", help="restrict speakers to oracle")
    parser.add_argument("--oracle_speakers", type=str, default=None, help="jsonl file with audio_filepath and speaker_label")
    parser.add_argument("--save", type=str, default=None, help="output file in format start_s \t end_s \t label")
    parser.add_argument("--no_convert", action="store_true", help="Skip audio conversion (use if file is already 16kHz mono WAV)")
    args = parser.parse_args()
    run(args)
