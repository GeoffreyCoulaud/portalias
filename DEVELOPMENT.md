## Local setup

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Setup the project using uv

```sh
uv sync
```

3. [Install pre-commit](https://pre-commit.com/#install)
4. Setup pre-commit for the project

```sh
pre-commit install
```


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