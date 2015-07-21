#!/bin/bash

COLLECTD=/usr/sbin/collectd
CONFIG_FILE=/etc/collectd/collectd.conf
CONFIG_TEMPLATE=/etc/collectd/collectd.conf.tmpl

get_metadata() {
    curl -f -s -S -H "Metadata-Flavor: Google" \
        "http://metadata.google.internal/computeMetadata/v1/$1"
}

get_collectd_endpoint() {
    for endpoint in collectd-gateway.google.stackdriver.com collectd-gateway.stackdriver.com; do
        if [[ "200" = $(curl -f -s -w "%{http_code}" --retry 1 -o /dev/null https://${endpoint}/v1/agent-test?stackdriver-apikey=${API_KEY} 2>/dev/null) ]]; then
            echo $endpoint
            return
        fi
    done
    echo 'Unable to determine collectd endpoint!' >&2
    return 1
}

IID=$(get_metadata instance/id)
API_KEY=$(get_metadata project/attributes/stackdriver-agent-key)
COLLECTD_ENDPOINT=$(get_collectd_endpoint)

sed -e "s/{IID}/$IID/; s/{API_KEY}/$API_KEY/; s|{COLLECTD_ENDPOINT}|$COLLECTD_ENDPOINT|" \
    $CONFIG_TEMPLATE > $CONFIG_FILE
exec $COLLECTD -f -C $CONFIG_FILE
