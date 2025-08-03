X2AGI_API_KEY=<YOUR_API_KEY>

REPO_ROOT=<PATH_TO_X2AGI_SPEECHKIT_REPO_ROOT>

## gRPC client
python client_grpc.py \
    --token ${X2AGI_API_KEY} \
    --lang en \
    --input_speakers ${REPO_ROOT}/example_data/postprocess_asr/en/azisu.result.speakers \
    --input_text ${REPO_ROOT}/example_data/postprocess_asr/en/azisu.result.text \
    --output_speakers azisu.result.speakers.pc \
    --output_text azisu.result.text.pc \
    --min_pause_to_separate 5.0

python client_grpc.py \
    --token ${X2AGI_API_KEY} \
    --lang ru \
    --input_speakers ${REPO_ROOT}/example_data/postprocess_asr/ru/garazh5min_2.result.speakers \
    --input_text ${REPO_ROOT}/example_data/postprocess_asr/ru/garazh5min_2.result.text \
    --output_speakers garazh5min_2.result.speakers.pc \
    --output_text garazh5min_2.result.text.pc \
    --min_pause_to_separate 5.0

## REST client
python client_rest.py \
    --token ${X2AGI_API_KEY} \
    --lang en \
    --input_speakers ${REPO_ROOT}/example_data/postprocess_asr/en/azisu.result.speakers \
    --input_text ${REPO_ROOT}/example_data/postprocess_asr/en/azisu.result.text \
    --output_speakers azisu.result.speakers.pc \
    --output_text azisu.result.text.pc \
    --min_pause_to_separate 5.0

python client_rest.py \
    --token ${X2AGI_API_KEY} \
    --lang ru \
    --input_speakers ${REPO_ROOT}/example_data/postprocess_asr/ru/garazh5min_2.result.speakers \
    --input_text ${REPO_ROOT}/example_data/postprocess_asr/ru/garazh5min_2.result.text \
    --output_speakers garazh5min_2.result.speakers.pc \
    --output_text garazh5min_2.result.text.pc \
    --min_pause_to_separate 5.0
