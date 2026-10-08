#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
output_dir="$repo_dir/research/real_world_validation"
mkdir -p "$output_dir"

mlx_pid=$(lsof -nP -iTCP:8000 -sTCP:LISTEN -t | head -1)
if [ -z "$mlx_pid" ]; then
  echo "No MLX server listening on port 8000" >&2
  exit 1
fi
python3 "$repo_dir/scripts/mlx_memory_guard.py" \
  --pid "$mlx_pid" --output "$output_dir/mlx_memory_status.json" &
guard_pid=$!
trap 'kill "$guard_pid" 2>/dev/null || true' EXIT INT TERM

docker build -f "$output_dir/Dockerfile" -t dct-mlx-research-controller:latest "$output_dir"
docker run --rm \
  --name dct-mlx-research-controller \
  --memory=1g --memory-swap=1g \
  --cpus=4 --pids-limit=128 \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --mount "type=bind,src=$repo_dir,dst=/workspace,readonly" \
  --mount "type=bind,src=$output_dir,dst=/workspace/research/real_world_validation" \
  -e MAX_STEPS="${MAX_STEPS:-12}" \
  dct-mlx-research-controller:latest
