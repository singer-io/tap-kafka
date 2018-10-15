# tap-kafka

This is a [Singer](https://singer.io) tap that produces JSON-formatted data following the [Singer spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md) from a Kafka source.

**This is a WIP**

# Quickstart

## Install the tap

```bash
git clone git@github.com:singer-io/tap-kafka.git # Clone this Repo
mkvirtualenv -p python3 tap-kafka                # Create a virtualenv
source tap-kafka/bin/activate                    # Activate the virtualenv
pip install -e .                                 # Install the local code
```

## Create a config.json

```
{
  "group_id": "1",
  "bootstrap_servers": "foo.com,bar.com",
  "topic": "messages",
  "reject_topic": "reject_topic",
  "schema": "<json schema>"
}
```

This tap's config requires a "schema" key which is a JSON document of JSON Schema formatted as a string. This document will be
loaded by the tap using `json.loads`. The schema describes the structure of the Kafka messages that are consumed off the topic.

## Run the tap in Discovery Mode

```
tap-kafka --config config.json --discover                # Should dump a Catalog to sdtout
tap-kafka --config config.json --discover > catalog.json # Capture the Catalog
```

## Add Metadata to the Catalog

Each entry under the Catalog's "stream" key will need the following metadata:

```
{
  "streams": [
    {
      "stream_name": "my_topic"
      "metadata": [{
        "breadcrumb": [],
        "metadata": {
          "selected": true,
        }
      }]
    }
  ]
}
```

## Run the tap in Sync Mode

```
tap-kafka --config config.json --properties catalog.json
```

The tap will write bookmarks to stdout which can be captured and passed as an optional `--state state.json` parameter to the tap for the next sync.

---

Copyright &copy; 2018 Stitch
