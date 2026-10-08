#!/bin/sh
set -eu

exec python /workspace/scripts/research_container_agent.py --max-steps "${MAX_STEPS:-12}"
