FROM python:alpine

# Install dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
RUN apk add --no-cache iptables

# Cleanup
RUN rm /tmp/requirements.txt

# Install app
COPY portalias /app/portalias
WORKDIR /app
ENV PYTHONPATH=/app

# Volumes
VOLUME /var/run/docker.sock
VOLUME /zones

ENV LOG_LEVEL=DEBUG
ENV INTERVAL=60
ENV DRY_RUN=false

CMD ["python", "-m", "portalias.main"]