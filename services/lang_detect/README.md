# Language Detection Service

Supported audio format: wav, 1 channel, 16000 Hz, LINEAR16_PCM (16-bit integers).
IMPORTANT: The client is expected to send the wav file as binary data without any modifications. Do not cut or change the header on the client side.
If you need to shorten the file, you can truncate and provide only the beginning, for example, 5-10 minutes.

Optionally, you can specify a list of allowed languages, e.g., [ru, en]. (Internally, the service's model supports many languages.)
Languages are denoted by two-letter strings according to the ISO 639-1 codes.

Example gRPC client call:

```bash
    python client_grpc.py \
    --token <YOUR_API_KEY> \
    --path example_ru.wav \
    --allowed_languages en,ru
```

See `lang_detect_service.proto` for the the full service definition and message structures.

Example REST client call:

```bash
    python client_rest.py \
    --token <YOUR_API_KEY> \
    --path example_ru.wav \
    --allowed_languages en,ru
```

The service operates synchronously and returns a structure like:

```json
{
  "allowed_language": "ru",
  "allowed_language_confidence": 0.95,
  "detected_language": "ru", 
  "detected_language_confidence": 0.95
}
```

If the most likely language is not among the allowed ones, the values in `allowed_language` and `detected_language` will differ, e.g.:
Example:

```json
{
  "allowed_language": "ru",
  "allowed_language_confidence": 0.4,
  "detected_language": "be",
  "detected_language_confidence": 0.93
}
```

This means the model recognized the language as Belarusian, but among the allowed languages [en, ru], the highest probability was for Russian.


## Audio Converter

The client scripts rely on a built-in audio converter, to use it you need to install `sox`.

```
sudo apt-get install sox libsox-fmt-all
```

If you do not need to convert audio, i.e. already have .wav 16000 Hz mono, you can turn off audio converter using option `--no_convert`.
