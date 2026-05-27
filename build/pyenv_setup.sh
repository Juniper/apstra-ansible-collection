#!/usr/bin/env bash
# Sourced automatically by every Jenkins sh step via BASH_ENV.
# Sets up pyenv so the correct Python version is available.
#
# IMPORTANT: unset BASH_ENV immediately so child processes spawned by pyenv
# (readlink, pyenv-init, etc.) do not re-source this file recursively,
# which would cause "Argument list too long" errors.
unset BASH_ENV

export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
export PATH="$PYENV_ROOT/bin:$HOME/.local/bin:$PATH"
eval "$(pyenv init -)"
