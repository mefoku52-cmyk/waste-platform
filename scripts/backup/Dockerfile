FROM postgres:18-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    age \
    bash \
    ca-certificates \
    coreutils \
    curl \
    findutils \
    grep \
    gzip \
    sed \
 && rm -rf /var/lib/apt/lists/* \
 && command -v age \
 && age --version \
 && pg_dump --version

WORKDIR /app

COPY scripts/backup/backup-prod.sh /app/backup-prod.sh

RUN chmod 0755 /app/backup-prod.sh

USER root

ENTRYPOINT ["bash", "/app/backup-prod.sh"]
CMD ["--upload"]
