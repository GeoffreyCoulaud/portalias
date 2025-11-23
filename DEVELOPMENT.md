## Compiling and running locally

```sh
docker build -t portalias . && \
docker run --rm -it \
    -e RULES_ID="portalias" \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    --cap-add NET_ADMIN \
    --cap-add NET_RAW \
    portalias
```