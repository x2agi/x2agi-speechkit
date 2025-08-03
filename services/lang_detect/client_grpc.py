import argparse
import grpc
import lang_detect.lang_detect_service_pb2
import lang_detect.lang_detect_service_pb2_grpc
import os
from audio_converter import convert_audio

def run(args):
    converted_path = None
    try:
        if args.no_convert:
            print("Skipping audio conversion")
            audio_path = args.path
        else:
            print("Converting audio to 16kHz mono WAV...")
            converted_path = convert_audio(args.path)
            audio_path = converted_path

        # Read audio data
        with open(audio_path, "rb") as f:
            audio_data = f.read(4 * 1024 * 1024)  # Read up to 4MB

        # gRPC setup and request
        with grpc.secure_channel(
            "lang-detect.x2agi.com:8443",
            grpc.ssl_channel_credentials(),
            options=[
                ("grpc.ssl_target_name_override", "lang-detect.x2agi.com"),
                ("grpc.default_authority", "lang-detect.x2agi.com"),
                ("grpc.keepalive_time_ms", 10000),
                ("grpc.max_receive_message_length", 50 * 1024 * 1024)
            ]
        ) as channel:
            stub = lang_detect.lang_detect_service_pb2_grpc.LangDetectorStub(channel)

            metadata = [
                ("authorization", f"Bearer {args.token}"),
            ]

            request = lang_detect.lang_detect_service_pb2.AudioLangDetectRequest(
                audio_data=audio_data,
                allowed_languages=args.allowed_languages.split(",") if args.allowed_languages else []
            )
            
            response = stub.DetectFromAudio(request, metadata=metadata)
            print(f"response={response}")

    finally:
        # Clean up temporary file
        if converted_path and os.path.exists(converted_path):
            os.remove(converted_path)

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
