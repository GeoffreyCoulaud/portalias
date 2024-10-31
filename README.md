# Portalias

Create port aliases on docker networks using iptables.

## Installation

The only supported installation method for portalias is using docker.  
Here is an example compose file:

```yml
networks:
  net1:
    driver: bridge
    labels:
      - "portalias.enabled=true"
  net2:

services:

  portalias:
    image: ghcr.io/geoffreycoulaud/portalias:latest
    environment:
      - RULES_ID=test-simple
      - LOG_LEVEL=DEBUG
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  web:
    image: httpd
    networks:
      net1:
      net2:
    labels:
      - "portalias.80=8888"
```

## Configuration

1. Add the `portalias.enabled` label to the networks you want to create aliases on.
2. Add labels for your aliases on the appropriate containers, using the appropriate format (see examples below)
3. Add portalias to your stack, setting the `RULES_ID` to something unique to your project. It is used to identify `iptables` rules handled by portalias.

Note that those aliases are availables *only* on the enabled networks, not the host. For that, you should use the docker port syntax.

## Example container labels
```
# Use port 8080 as an alias for port 80
portalias.80=8080

# Same, but explicit TCP only
portalias.80.tcp=8080

# Add UDP support
portalias.80.tcp,udp=8080

# Set multiple aliases
portalias.80=8080,7070

# Set multiple protocols and aliases
portalias.80.tcp,udp=8080,7070
```