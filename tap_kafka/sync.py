import singer
from singer import utils, metadata
from kafka import KafkaConsumer, OffsetAndMetadata, TopicPartition
import pdb
import sys
import json
import time
import copy
import tap_kafka.common as common

LOGGER = singer.get_logger()
UPDATE_BOOKMARK_PERIOD = 1000

def write_schema_message(schema_message):
    sys.stdout.write(json.dumps(schema_message) + '\n')
    sys.stdout.flush()

def send_schema_message(stream):
    md_map = metadata.to_map(stream['metadata'])
    pks =  md_map.get((), {}).get('table-key-properties', [])

    schema_message = {'type' : 'SCHEMA',
                      'stream' : stream['tap_stream_id'],
                      'schema' : stream['schema'],
                      'key_properties' : pks,
                      'bookmark_properties': pks}
    write_schema_message(schema_message)


def do_sync(kafka_config, catalog, state):
    for stream in catalog['streams']:
        sync_stream(kafka_config, stream, state)

def sync_stream(kafka_config, stream, state):
    consumer = KafkaConsumer(kafka_config['topic'],
                             group_id=kafka_config['group_id'],
                             enable_auto_commit=False,
                             consumer_timeout_ms=10000,
                             auto_offset_reset='earliest',
                             value_deserializer=lambda m: json.loads(m.decode('ascii')),
                             bootstrap_servers=kafka_config['bootstrap_servers'])

    send_schema_message(stream)
    stream_version = singer.get_bookmark(state, stream['tap_stream_id'], 'version')
    if stream_version is None:
        stream_version = int(time.time() * 1000)

    state = singer.write_bookmark(state,
                                  stream['tap_stream_id'],
                                  'version',
                                  stream_version)
    singer.write_message(singer.StateMessage(value=copy.deepcopy(state)))
    activate_version_message = singer.ActivateVersionMessage(stream=stream['tap_stream_id'], version=stream_version)



    singer.write_message(activate_version_message)

    time_extracted = utils.now()
    rows_saved = 0
    for message in consumer:
        LOGGER.info("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                                   message.offset, message.key,
                                                   message.value))
        record_message = singer.RecordMessage(stream=stream['tap_stream_id'], record=message.value, time_extracted=time_extracted)

        singer.write_message(record_message)
        rows_saved = rows_saved + 1

        state = singer.write_bookmark(state,
                                      stream['tap_stream_id'],
                                      'offset',
                                      message.offset)

        if rows_saved % UPDATE_BOOKMARK_PERIOD == 0:
            singer.write_message(singer.StateMessage(value=copy.deepcopy(state)))

        #commit offsets because we processed the message
        tp = TopicPartition(message.topic, message.partition)
        consumer.commit({tp: OffsetAndMetadata(message.offset + 1, None)})

    singer.write_message(singer.StateMessage(value=copy.deepcopy(state)))
