FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-scapy \
    python3-pytest \
    iproute2 \
    net-tools \
    tcpdump \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY setup_ecmp.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/setup_ecmp.sh

COPY test_ecmp.py /tests/

COPY run_tests.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/run_tests.sh

WORKDIR /tests

ENTRYPOINT ["/usr/local/bin/run_tests.sh"]
