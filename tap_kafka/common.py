def default_streams(kafka_config):
    return [{'tap_stream_id': kafka_config['topic'], 'metadata' : [], 'schema' : {}}]
