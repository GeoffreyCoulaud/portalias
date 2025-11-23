#!/bin/bash

# The portalias repo is mounted at /mnt/portalias

# 1. Create two docker networks
#     a. one with the portalias label (net1)
#     b. another with no label (net2)
# 2. Run a service having both networks
# 3. Run portalias in the background
# 4. Ensure that the service is reachable on net1 from port 8888
# 5. Ensure that the service is NOT reachable on net2 from port 8888

set -euxo pipefail

function get_container_ip_on_network() {
    local container_id=$1
    local network_name=$2

    docker inspect $network_name \
    | jq ".[0].Containers[\"$container_id\"].IPv4Address" \
    | cut -d'/' -f1 \
    | tr -d '"'
}

function build_portalias() {
    cd /mnt/portalias
    docker build -t portalias .
}

function run_portalias() {
    docker run \
    -e RULES_ID="portalias" \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    --cap-add NET_ADMIN \
    --cap-add NET_RAW \
    portalias
}

function run_service() {
    docker run -d \
    --label "portalias.80=8888" \
    --network net1 \
    --network net2 \
    strm/helloworld-http
}

function test_connectivity() {
    local network=$1
    local address=$2
    local port=$3
    docker run --rm --network $network alpine/curl \
    -sL -w %{http_code} $address:$port -o /dev/null
}

# --------------------------------------------------------------------------------------
# Test code
# --------------------------------------------------------------------------------------

# --- Given
net1=$(docker network create --label "portalias.enabled=true" net1)
net2=$(docker network create net2)
service_id=$(run_service)
service_net1_ip=$(get_container_ip_on_network $service_id $net1)
service_net2_ip=$(get_container_ip_on_network $service_id $net2)
build_portalias

# --- When
portalias_id=$(run_portalias)
sleep 5

# --- Then
# Sanity checks, 80 should be reachable on both networks
test $(test_connectivity $net1 $service_net1_ip 80) -eq 200 
test $(test_connectivity $net2 $service_net2_ip 80) -eq 200
# Check portalias behavior
test $(test_connectivity $net1 $service_net1_ip 8888) -eq 200 # OK
test $(test_connectivity $net2 $service_net2_ip 8888) -eq 000 # connection refused

# --- Cleanup
docker rm -f $service_id
docker rm -f $portalias_id
docker network rm $net1
docker network rm $net2