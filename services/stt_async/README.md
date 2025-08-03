# Speech Recognition and Speaker Diarization Service

The service operates asynchronously. See the method definitions for the `AsyncRecognizer` service in the `stt_async_service.proto` file.
Requests are transmitted via the gRPC protocol.
Supported languages : Russian and English.
Supported audio format : WAV, 1 channel, 16000Hz, LINEAR16_PCM (16-bit integers).
IMPORTANT: The client must send the WAV file as raw binary data without any modifications. Do not trim or alter the header on the client side.

Transcription is returned as lowercase text without punctuation.
The number of speakers for diarization is determined automatically.

## Running the gRPC client:

Russian example:

```bash
python client_grpc.py \
    --token <YOUR_API_KEY> \
    --lang ru \
    --path garazh5min_2.wav \
    --save garazh5min_2.result
```

English example:

```bash
python client_grpc.py \
    --token <YOUR_API_KEY> \
    --lang en \
    --path godfather_lasvegas.wav \
    --save godfather_lasvegas.result
```

When using the `--save` option, the client saves recognition results to `<SAVE_FILE>.speakers` and `<SAVE_FILE>.text` files with timestamped labels.
These label files can be imported into Audacity (File → Import → Labels) to review the annotated audio.
Speakers are labeled as `Speaker 1`, `Speaker 2`, etc., or `[unidentifiable]`.

## Running the gRPC client with speaker voice samples

```bash
python client_grpc.py \
    --token <YOUR_API_KEY> \
    --lang en \
    --path godfather_lasvegas.wav \
    --save godfather_lasvegas.result \
    --oracle_speakers godfather_lasvegas_oracle.json \
    --restrict_to_oracle_speaker_labels
```

The client reads speaker data from a `.json` file and sends it to the service at the start of the session. See example in `godfather_lasvegas_oracle.json`:

```jsonl
{"audio_filepath": "godfather_oracle/JOHNNY.wav", "speaker_label": "JOHNNY"}
{"audio_filepath": "godfather_oracle/JOHNNY-2.wav", "speaker_label": "JOHNNY"}
{"audio_filepath": "godfather_oracle/MICHAEL.wav", "speaker_label": "MICHAEL"}
{"audio_filepath": "godfather_oracle/MICHAEL-2.wav", "speaker_label": "MICHAEL"}
```

Speakers matching the provided samples will use labels from the json file. New speakers will be labeled as `Speaker 1`, `Speaker 2`, etc., or `[unidentifiable]`.
The `--restrict_to_oracle_speaker_labels` option prevents the service from adding speakers not present in the sample data.


## Using REST Instead of gRPC

For REST API usage, see the `client_rest.py`. All the above examples work - just replace `client_grpc.py` with `client_rest.py` 

## Processing long files

The service is capable of processing long audio files lasting several hours, if the account balance is sufficient. Charges are applied exclusively for successfully finished operations."

## Other languages

You can try other languages as well if you only need speaker diarization. Speaker labeling is likely to work, but the text transcript will be incorrect.

## Audio Converter

The client scripts rely on a built-in audio converter, to use it you need to install `sox`.

```
sudo apt-get install sox libsox-fmt-all
```

If you do not need to convert audio, i.e. already have .wav 16000 Hz mono, you can turn off audio converter using option `--no_convert`.
