X2AGI_API_KEY=<YOUR_API_KEY>

REPO_ROOT=<PATH_TO_X2AGI_SPEECHKIT_REPO_ROOT>

python client_grpc.py \
    --token ${X2AGI_API_KEY} \
    --path ${REPO_ROOT}/example_data/lang_detect/example.wav \
    --allowed_languages en,ru

python client_rest.py \
    --token ${X2AGI_API_KEY} \
    --path ${REPO_ROOT}/example_data/lang_detect/example.wav \
    --allowed_languages en,ru
