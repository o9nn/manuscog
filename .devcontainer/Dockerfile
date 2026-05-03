# =============================================================================
# Inferno-OS Cognitive Kernel Development Container
# Multi-stage build: base → build → development
# Derived from inferno-os/inferno-os official Dockerfile
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Build Inferno-OS from source
# ---------------------------------------------------------------------------
FROM ubuntu:22.04 AS inferno-builder

ARG DEBIAN_FRONTEND=noninteractive
ARG INFERNO_ROOT=/usr/inferno

# Build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    gcc-multilib \
    libc6-dev \
    libc6-dev-i386 \
    libx11-dev \
    libxext-dev \
    libx11-dev:i386 \
    libxext-dev:i386 \
    git \
    ca-certificates \
    xorg-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone Inferno-OS from the official repository
RUN git clone --depth 1 https://github.com/inferno-os/inferno-os.git ${INFERNO_ROOT}

WORKDIR ${INFERNO_ROOT}

# Configure mkconfig for Linux/amd64 hosted build
RUN echo "ROOT=${INFERNO_ROOT}" > mkconfig && \
    echo "TKSTYLE=std" >> mkconfig && \
    echo "SYSHOST=Linux" >> mkconfig && \
    echo "SYSTARG=Linux" >> mkconfig && \
    echo "OBJTYPE=amd64" >> mkconfig && \
    echo 'OBJDIR=$SYSTARG/$OBJTYPE' >> mkconfig && \
    echo '<$ROOT/mkfiles/mkhost-$SYSHOST' >> mkconfig && \
    echo '<$ROOT/mkfiles/mkfile-$SYSTARG-$OBJTYPE' >> mkconfig

# Bootstrap mk and build Inferno
RUN ./makemk.sh
ENV PATH="${INFERNO_ROOT}/Linux/amd64/bin:${PATH}"
RUN mk nuke && mk install

# ---------------------------------------------------------------------------
# Stage 2: Development environment
# ---------------------------------------------------------------------------
FROM ubuntu:22.04 AS development

ARG DEBIAN_FRONTEND=noninteractive
ARG INFERNO_ROOT=/usr/inferno
ARG CLUSTER_NODES=3
ARG ENABLE_GUI=true

LABEL maintainer="manuscog <manuscog@danregima.com>"
LABEL description="Inferno-OS Cognitive Kernel Development Environment"
LABEL org.opencontainers.image.source="https://github.com/danregima/manuscog"

# Runtime and development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # --- Core build tools ---
    build-essential \
    gcc \
    gdb \
    valgrind \
    strace \
    ltrace \
    make \
    cmake \
    # --- X11 / GUI support ---
    libx11-6 \
    libxext6 \
    libx11-dev \
    libxext-dev \
    x11-apps \
    xauth \
    # --- Networking / 9P ---
    net-tools \
    iproute2 \
    iputils-ping \
    socat \
    ncat \
    tcpdump \
    wireshark-common \
    tshark \
    # --- Editors / IDE ---
    vim \
    neovim \
    nano \
    tmux \
    screen \
    # --- Version control ---
    git \
    git-lfs \
    # --- Python (for cognitive kernel scripts) ---
    python3 \
    python3-pip \
    python3-venv \
    # --- Utilities ---
    curl \
    wget \
    jq \
    tree \
    htop \
    less \
    file \
    unzip \
    zip \
    ca-certificates \
    locales \
    sudo \
    # --- Documentation ---
    man-db \
    manpages-dev \
    && rm -rf /var/lib/apt/lists/*

# Set locale
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Copy built Inferno from builder stage
COPY --from=inferno-builder ${INFERNO_ROOT} ${INFERNO_ROOT}

# Set Inferno environment
ENV INFERNO_ROOT=${INFERNO_ROOT}
ENV EMU=${INFERNO_ROOT}/Linux/amd64/bin/emu
ENV LIMBO=${INFERNO_ROOT}/Linux/amd64/bin/limbo
ENV PATH="${INFERNO_ROOT}/Linux/amd64/bin:${PATH}"

# Create inferno user
RUN groupadd -g 1000 inferno && \
    useradd -m -u 1000 -g inferno -s /bin/zsh inferno && \
    echo "inferno ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/inferno

# Create cluster data directories
RUN mkdir -p /var/inferno/cluster && \
    for i in $(seq 0 $((CLUSTER_NODES - 1))); do \
        mkdir -p /var/inferno/cluster/node-${i}/{namespace,registry,keys,logs}; \
    done && \
    chown -R inferno:inferno /var/inferno

# Create workspace directory
RUN mkdir -p /workspace && chown inferno:inferno /workspace

# Install Python packages for cognitive kernel development
RUN pip3 install --no-cache-dir \
    networkx \
    matplotlib \
    numpy \
    pyyaml \
    flask \
    requests \
    rich \
    click

# Copy devcontainer scripts
COPY scripts/ /workspace/.devcontainer/scripts/
RUN chmod +x /workspace/.devcontainer/scripts/*.sh

# Copy Limbo syntax and editor configs
COPY limbo-support/ /usr/share/inferno/limbo-support/

USER inferno
WORKDIR /workspace

# Default: start emu in text mode
CMD ["emu", "-c1"]
