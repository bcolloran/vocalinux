FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG NODE_MAJOR=22

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  alsa-utils \
  build-essential \
  ca-certificates \
  cmake \
  curl \
  ffmpeg \
  git \
  git-lfs \
  glslang-tools \
  gobject-introspection \
  gir1.2-ayatanaappindicator3-0.1 \
  gir1.2-gtk-3.0 \
  gir1.2-ibus-1.0 \
  libasound2-dev \
  libcairo2-dev \
  libgirepository-2.0-dev \
  libpulse0 \
  libvulkan-dev \
  libvulkan1 \
  pkg-config \
  portaudio19-dev \
  pulseaudio-utils \
  python3 \
  python3-dev \
  python3-gi \
  python3-gi-cairo \
  python3-pip \
  python3-venv \
  rsync \
  unzip \
  vulkan-tools \
  wget \
  wl-clipboard \
  wtype \
  xclip \
  xdotool \
  && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - \
  && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
  && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | tee /etc/apt/sources.list.d/github-cli.list \
  && apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y gh nodejs \
  && npm install -g @anthropic-ai/claude-code \
  && npm cache clean --force \
  && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv \
  && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
  && chown -R vscode:vscode /opt/venv

USER vscode
ENV VIRTUAL_ENV=/opt/venv
ENV PATH=/opt/venv/bin:$PATH
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /workspaces/vocalinux
