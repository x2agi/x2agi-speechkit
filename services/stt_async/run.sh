X2AGI_API_KEY=<YOUR_API_KEY>

REPO_ROOT=<PATH_TO_X2AGI_SPEECHKIT_REPO_ROOT>

## gRPC client
python client_grpc.py \
    --token ${X2AGI_API_KEY} \
    --lang ru \
    --path ${REPO_ROOT}/example_data/stt_async/ru/garazh5min_2.wav \
    --save garazh5min_2.result

python client_grpc.py \
    --token ${X2AGI_API_KEY} \
    --lang en \
    --path ${REPO_ROOT}/example_data/stt_async/en/godfather_lasvegas.wav \
    --save godfather_lasvegas.result

python client_grpc.py \
    --token ${X2AGI_API_KEY} \
    --lang ru \
    --path ${REPO_ROOT}/example_data/stt_async/ru/garazh5min_2.wav \
    --save garazh5min_2.result \
    --oracle_speakers ${REPO_ROOT}/example_data/stt_async/ru/garazh_oracle.json 

python client_grpc.py \
    --token ${X2AGI_API_KEY} \
    --lang en \
    --path ${REPO_ROOT}/example_data/stt_async/en/godfather_lasvegas.wav \
    --save godfather_lasvegas.result \
    --oracle_speakers ${REPO_ROOT}/example_data/stt_async/en/godfather_lasvegas_oracle.json 

## REST client
python client_rest.py \
    --token ${X2AGI_API_KEY} \
    --lang ru \
    --path ${REPO_ROOT}/example_data/stt_async/ru/garazh5min_2.wav \
    --save garazh5min_2.result

python client_rest.py \
    --token ${X2AGI_API_KEY} \
    --lang en \
    --path ${REPO_ROOT}/example_data/stt_async/en/godfather_lasvegas.wav \
    --save godfather_lasvegas.result

python client_rest.py \
    --token ${X2AGI_API_KEY} \
    --lang ru \
    --path ${REPO_ROOT}/example_data/stt_async/ru/garazh5min_2.wav \
    --save garazh5min_2.result \
    --oracle_speakers ${REPO_ROOT}/example_data/stt_async/ru/garazh_oracle.json 

python client_rest.py \
    --token ${X2AGI_API_KEY} \
    --lang en \
    --path ${REPO_ROOT}/example_data/stt_async/en/godfather_lasvegas.wav \
    --save godfather_lasvegas.result \
    --oracle_speakers ${REPO_ROOT}/example_data/stt_async/en/godfather_lasvegas_oracle.json 
