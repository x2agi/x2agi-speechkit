# LLM-based ASR Post-Processing service

The `postprocess_asr` service takes as input the result text files from diarization and ASR (`stt_async`) service. It restores punctuation and capitalization, corrects typos.
The service operates asynchronously. See the method definitions for the `AsyncAsrPostprocessor` service in the `postprocess_asr_service.proto` file.

## Running the gRPC client:

```bash
python client_grpc.py \
  --token <YOUR_API_KEY> \
  --lang en \
  --input_speakers godfather_lasvegas.result.speakers \
  --input_text godfather_lasvegas.result.text \
  --output_speakers godfather_lasvegas.result.speakers.pc \
  --output_text godfather_lasvegas.result.text.pc \
  --min_pause_to_separate 5.0
```

## Running the REST client:

```bash
python client_rest.py \
  --token <YOUR_API_KEY> \
  --lang en \
  --input_speakers godfather_lasvegas.result.speakers \
  --input_text godfather_lasvegas.result.text \
  --output_speakers godfather_lasvegas.result.speakers.pc \
  --output_text godfather_lasvegas.result.text.pc \
  --min_pause_to_separate 5.0
```

In the `--input_speakers` and `--input_text` options, you provide files received from ASR. These files must have the same number of lines, and their timestamps must be the same.
The `--output_speakers` and `--output_text` options specify the output filenames where results will be saved. These outputs will follow the same format as the input files, but with:

* Potentially fewer lines (if consecutive identical speakers are merged)
* Normalized text

The `--min_pause_to_separate` option controls the minimum pause duration (in seconds) between identical speakers that prevents their text from being merged.
To force merging of identical speakers always, set this value to a large number (e.g., `999999.0`).

## Monologue Mode
If the `--as_monologue` flag is added:

* All speakers are relabeled as "Speaker 1".
* Text merging is still controlled by `--min_pause_to_separate` (see above).
* This is useful when you know in advance that the audio contains only one speaker.
