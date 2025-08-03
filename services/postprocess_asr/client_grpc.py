import argparse
import grpc
import json
import os
import time
import uuid
import postprocess_asr.postprocess_asr_service_pb2
import postprocess_asr.postprocess_asr_service_pb2_grpc

def run(args):
    # Generate job_id on the client before any requests
    job_id = str(uuid.uuid4())

    # Установите соединение с сервером.
    with grpc.secure_channel(
        "postprocess-asr.x2agi.ru:8443",
        grpc.ssl_channel_credentials(),
        options=[
            ("grpc.ssl_target_name_override", "postprocess-asr.x2agi.ru"),  # Force SNI
            ("grpc.default_authority", "postprocess-asr.x2agi.ru"),
            # Recommended optimizations:
            ("grpc.keepalive_time_ms", 10000),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024)
        ]
    ) as channel:
        stub = postprocess_asr.postprocess_asr_service_pb2_grpc.AsyncAsrPostprocessorStub(channel)

        # Read the entire speakers file content
        with open(args.input_speakers, "r", encoding="utf-8") as f:
            speakers = f.read()

        # Read the entire text file content
        with open(args.input_text, "r", encoding="utf-8") as f:
            utterances = f.read()

        if args.lang not in ["en", "ru"]:
            raise ValueError(f"expected --lang: 'en' or 'ru', got '{args.lang}'")

        request = postprocess_asr.postprocess_asr_service_pb2.PostprocessAsrRequest(
            speakers=speakers,
            utterances=utterances,
            min_pause_to_separate=args.min_pause_to_separate,
            as_monologue=args.as_monologue,
            language=args.lang
        )

        initial_metadata = [
            ("authorization", f"Bearer {args.token}"),
            ("x-job-id", job_id),
        ]

        operation = stub.PostprocessAsr(request, metadata=initial_metadata)
        # operation.id is returned by the server, but Envoy routing is pinned by x-job-id
        print(f"server returned operation ID = {operation.id}")

        # Poll the progress until the status is "completed"
        while True:
            get_progress_request = postprocess_asr.postprocess_asr_service_pb2.GetProgressRequest(operation_id=operation.id)
            progress_response = stub.GetProgress(get_progress_request, metadata=initial_metadata)

            status, progress = progress_response.status, progress_response.progress
            print(f"Progress: {progress}%, Status: {status}")

            if status == "completed":
                break  # Exit the loop when the operation is completed
            elif status == "failed":
                raise RuntimeError("Asr postprocessor operation failed: please contact support.")

            time.sleep(2)  # Wait before polling again

        # Call GetRecognition
        get_recognition_request = postprocess_asr.postprocess_asr_service_pb2.GetRecognitionRequest(operation_id=operation.id)
        response = stub.GetRecognition(get_recognition_request, metadata=initial_metadata)

        print(f"response.speakers={response.speakers}")
        print(f"response.text={response.utterances}")

        with open(args.output_speakers, "w", encoding="utf-8") as out:
            out.write(response.speakers + "\n")
        with open(args.output_text, "w", encoding="utf-8") as out:
            out.write(response.utterances + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", type=str, required=True, help="IAM token or API key")
    parser.add_argument("--lang", type=str, required=True, help="Language of input text: ['ru', 'en']")
    parser.add_argument("--input_speakers", type=str, required=True, help="input file with timestamps and speaker labels")
    parser.add_argument("--input_text", type=str, required=True, help="input file with timestamps and utterances")
    parser.add_argument("--output_speakers", type=str, required=True, help="input file with timestamps and speaker labels")
    parser.add_argument("--output_text", type=str, required=True, help="input file with timestamps and utterances")
    parser.add_argument("--min_pause_to_separate", type=float, default=5.0, help="minimum pause (sec) to keep separate adjacent utterances for same speaker, otherwise they will be merged, default=5.0")
    parser.add_argument("--as_monologue", action="store_true", help="force single speaker")

    args = parser.parse_args()
    run(args)
