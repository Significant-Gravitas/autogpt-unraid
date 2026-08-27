ARG AUTOGPT_IMAGE=significantgravitas/autogpt@sha256:9a97378805acd43b4bf12bac463f80ff10b7b3743146f74e35c7b7281d2ad48b
FROM ${AUTOGPT_IMAGE}
ARG AUTOGPT_IMAGE

LABEL org.opencontainers.image.title="AutoGPT Fully Local for Unraid" \
      org.opencontainers.image.description="AutoGPT single-container runtime with an internal local-model compatibility adapter" \
      org.opencontainers.image.source="https://github.com/Significant-Gravitas/autogpt-unraid" \
      org.opencontainers.image.licenses="LicenseRef-PolyForm-Shield-1.0.0 AND SSPL-1.0" \
      org.opencontainers.image.base.name="${AUTOGPT_IMAGE}"

ENV LISTEN_HOST=127.0.0.1 \
    LISTEN_PORT=8098 \
    EMBED_PAD_DIM=1536 \
    EMBED_MAX_TOKENS=2048 \
    CHAT_USE_LOCAL=true \
    CHAT_BASE_URL=http://127.0.0.1:8098/v1 \
    CHAT_API_KEY=local \
    GRAPHITI_LLM_BASE_URL=http://127.0.0.1:8098/v1 \
    GRAPHITI_LLM_API_KEY=local \
    GRAPHITI_EMBEDDER_BASE_URL=http://127.0.0.1:8098/raw/v1 \
    GRAPHITI_EMBEDDER_API_KEY=local \
    GRAPHITI_EMBEDDER_MODEL=nomic-embed-text \
    STORE_EMBEDDING_MODEL=nomic-embed-text

RUN groupadd --system --gid 10007 autogpt-local-adapter \
    && useradd --system --uid 10007 --gid autogpt-local-adapter \
      --home-dir /nonexistent --shell /usr/sbin/nologin autogpt-local-adapter \
    && install -d -m 0755 -o root -g root \
      /opt/autogpt-local /usr/share/licenses/autogpt-local-adapter

COPY --chown=0:0 --chmod=0555 router/proxy.py router/healthcheck.py local-image/run_adapter.py /opt/autogpt-local/
COPY --chown=0:0 --chmod=0444 LICENSE /usr/share/licenses/autogpt-local-adapter/LICENSE
COPY --chown=0:0 --chmod=0444 local-image/supervisord-local-adapter.conf /tmp/supervisord-local-adapter.conf
COPY --chown=0:0 --chmod=0555 local-image/install.py /tmp/install-local-adapter.py
COPY --chown=0:0 --chmod=0555 local-image/healthcheck.sh /opt/autogpt-local/healthcheck.sh

RUN /app/autogpt_platform/backend/.venv/bin/python /tmp/install-local-adapter.py \
      --config /opt/autogpt/single-container/supervisor/supervisord.conf \
      --fragment /tmp/supervisord-local-adapter.conf \
      --healthcheck /usr/local/bin/autogpt-healthcheck \
    && rm -f /tmp/install-local-adapter.py /tmp/supervisord-local-adapter.conf

HEALTHCHECK --interval=30s --timeout=45s --start-period=5m --retries=5 \
    CMD ["/opt/autogpt-local/healthcheck.sh"]
