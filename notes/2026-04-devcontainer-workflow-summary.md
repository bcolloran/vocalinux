# Devcontainer Workflow Summary

## Purpose

This note summarizes the devcontainer work that was done for Vocalinux and the
workflow we decided to use for now.

## Final Goal We Chose

The chosen security boundary is:

- agents inside the devcontainer may freely modify this repo
- those repo changes should immediately appear on the host checkout
- agents should not be able to write to other host folders
- agent settings, editor preferences, and sign-in state should still be
  available inside the container
- host audio access is allowed
- host GUI session access is not enabled yet

This means the repo itself is considered recoverable, but the rest of the host
should stay out of bounds.

## What Was Changed

### 1. Replaced the old stack-specific image 
The container image is focused on Vocalinux's actual needs.

The devcontainer image now includes:

- Python development tooling
- GTK 3 and GI bindings
- Ayatana AppIndicator and IBus packages
- PortAudio and PulseAudio utilities
- Vulkan tools
- `xdotool`, `wtype`, `xclip`, `wl-clipboard`
- Node.js, GitHub CLI, and Claude Code

### 2. Made the repo itself the writable workspace

The current `workspaceMount` in `.devcontainer/devcontainer.json` bind-mounts
the repo directly:

```json
"workspaceMount": "source=${localWorkspaceFolder},target=/workspaces/vocalinux,type=bind,consistency=cached"
```

That means:

- the repo is writable from inside the container
- file changes are immediately reflected on the host checkout
- there is no extra sync step between container and host for repo contents

### 3. Kept other host access read-only

The following host paths are mounted read-only into the container and then
bootstrapped into container-local writable locations as needed:

- `~/.codex`
- `~/.claude`
- `~/.config/gh`
- `~/.config/Code/User`
- `~/.config/pulse`
- `~/.gitconfig`

This gives the container access to useful state without making those host files
directly writable.

### 4. Re-enabled autonomous agent defaults

Since the container itself is the intended sandbox, the more permissive
agent/editor defaults were explicitly re-enabled inside the devcontainer:

- Claude permission bypass
- auto-approve style behavior
- autopilot-oriented settings

The idea is that the container should allow fast, autonomous work inside the
repo, while the host filesystem boundary is enforced by mount design.

### 5. Added host audio access

The container is configured with:

- `/dev/snd`
- Pulse/PipeWire Pulse socket access via `${XDG_RUNTIME_DIR}/pulse`

This supports microphone and audio-related testing from inside the container,
while avoiding broader GUI/session integration.

## Workflow We Discussed

### Current baseline workflow

This is the workflow we chose to start with:

1. Open the repo in the devcontainer.
2. Let agents work directly inside the mounted repo.
3. Run the application or tests on the host when needed.

Because the repo is the same checkout in both places, host-side commands see the
same files the agent edited in the container.

Example host-side commands:

```bash
pytest -m "not audio"
vocalinux --debug
```

## Why This Workflow Was Chosen

An earlier approach used a Docker volume as an isolated writable copy of the
repo, then required an explicit export step back to the host. That was safer for
the repo itself, but clunkier.

We replaced that with the simpler repo-bind-mount model because:

- repo damage is considered acceptable and recoverable from GitHub
- the main thing we want to protect is the rest of the host
- direct repo edits make the development loop much smoother

So the current model intentionally favors autonomy and ease of use inside the
repo, while still limiting host impact outside it.

## GUI / Tray Testing Discussion

We also discussed how GUI testing would work for Vocalinux.

Important distinction:

- showing normal GTK windows requires display access
- showing a system tray icon also requires desktop-session integration,
  especially session D-Bus and StatusNotifier/AppIndicator support

For now, host X11 and Wayland session sockets are **not** mounted into the
container.

That means:

- host audio testing is enabled
- full GTK/tray testing from inside the container is not enabled yet
- the current safe approach is still to run GUI tests on the host

## Options We Discussed For Later

If the current workflow becomes too limiting, the possible next steps discussed
were:

1. Host-integrated GUI testing
   - best UX
   - weakest isolation
   - tray would appear in the real host desktop session

2. Nested desktop inside the container
   - better isolation than host-integrated GUI access
   - tray and GTK UI would run in a separate container desktop

3. Keep the current model
   - simplest
   - strongest host-session isolation among the options discussed so far

For now, the selected baseline remains:

- container dev
- host run/test for GUI behavior
- no direct host GUI session access from the container

## Current State Summary

At this point the devcontainer is designed so that:

- this repo is writable from the container
- other host locations are not writable from the container
- shared agent and token state is available
- audio access is available
- autonomous agent defaults are enabled
- GUI desktop integration is deferred until there is a clear need
