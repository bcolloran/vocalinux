# Devcontainer Notes

This devcontainer is tailored for Vocalinux rather than the old Godot/Rust stack.

## Isolation model

- The repo itself is bind-mounted at `/workspaces/vocalinux`.
- Agents can read and write inside this repo, and those file changes are reflected
  on the host checkout.
- No other host folders are mounted writable.
- `prepare-home.sh` fixes ownership on volume-backed config directories before
  settings and tokens are copied in.
- Everything outside the repo stays container-local unless explicitly mounted.

## Shared settings and tokens

Selected host config is mounted read-only under `/host-home` and then copied into
container-local volumes:

- `~/.codex`
- `~/.claude`
- `~/.config/gh`
- `~/.config/Code/User`
- `~/.config/pulse`
- `~/.gitconfig`

This keeps the host as the source of truth without granting the container write
access back to those files.

## Audio access

The container gets:

- `/dev/snd`
- the host PulseAudio or PipeWire Pulse socket via `${XDG_RUNTIME_DIR}/pulse`

Inside the container, audio clients should use:

```bash
echo "$PULSE_SERVER"
```

If your host uses a nonstandard audio setup, adjust the `runArgs` or mounts in
`devcontainer.json`.

## Display access

This baseline does not mount X11 or Wayland display sockets yet. That keeps the
host integration surface smaller while still covering the requirements you asked
for here: isolated writes, shared settings and tokens, and host audio.

## Development Workflow

This is now the intended baseline:

1. Open the repo in the devcontainer.
2. Let agents work directly in the mounted repo.
3. Run the app or tests on the host whenever you want, since the repo contents
   are already the same checkout.

That gives agents autonomy within the repo while keeping the rest of the host
outside their write boundary.
