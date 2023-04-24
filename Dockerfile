FROM alpine

USER root

RUN apk update && \
    apk add python3 curl && \
    curl -s https://bootstrap.pypa.io/get-pip.py | python3 && \
    apk del curl

COPY requirements.txt /tmp/requirements.txt

RUN pip3 install -r /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt && \
    adduser -D appuser

COPY --chown=appuser:appuser app /app

WORKDIR /app
USER appuser

ENV PYTHONUNBUFFERED=1

CMD [ "python3", "main.py" ]