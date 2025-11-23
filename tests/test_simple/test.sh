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

function get_container_id() {
    local container_name=$1

    docker container inspect "$container_name" \
    | jq -r '.[0].Id'
}

function get_container_ip_on_network() {
    local container_name=$1
    local network_name=$2

    container_id=$(get_container_id $container_name)

    docker inspect $network_name \
    | jq ".[0].Containers[\"$container_id\"].IPv4Address" \
    | cut -d'/' -f1 \
    | tr -d '"'
}

function test_connectivity() {
    local address=$1

    docker exec client curl -sL -o /dev/null -w '%{http_code}' "$address"
}

function expect_http_status(){
    local address=$1
    local expected_status=$2

    local http_code=$(test_connectivity $address)
    if [[ "$http_code" != "$expected_status" ]]; then
        echo "Expected HTTP $expected_status but got $http_code from $address"
        exit 1
    fi
}

# --------------------------------------------------------------------------------------
# Test code
# --------------------------------------------------------------------------------------

# --- Given
echo "[given] Setup docker compose environment"
docker compose up --quiet-pull --wait -d
echo "[given] Get server IPs"
server_net1_ip=$(get_container_ip_on_network server test_simple_net1)
server_net2_ip=$(get_container_ip_on_network server test_simple_net2)

# --- When
echo "[when] Give some time for portalias to do its job"
sleep 3

# --- Then
echo "[then] Sanity checks, 80 should be reachable on both networks"
expect_http_status $server_net1_ip:80 200
expect_http_status $server_net2_ip:80 200
echo "[then] Check portalias behavior"
expect_http_status $server_net1_ip:8888 200 # OK
expect_http_status $server_net2_ip:8888 000 # connection refused

# --- Cleanup
echo "[cleanup] Tear down docker compose environment"
docker compose down