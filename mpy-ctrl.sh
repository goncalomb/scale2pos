#!/usr/bin/env bash

# MicroPython environment control utility.
# Author: Gonçalo MB <me@goncalomb.com>
# Version: 0.1

set -euo pipefail
cd -- "$(dirname -- "$0")"

. mpy-ctrl.conf

setup_check() {
    if [ ! -d ".venv" ] || [ ! -d ".mpy" ]; then
        echo "run setup first" && exit 1
    fi
    . .venv/bin/activate
}

mpy_hard_reset() {
    trap - EXIT INT TERM
    echo "resetting..."
    # mpremote can fail ungracefully if the board is in an invalid state
    # e.g. configured as a custom USB device
    if ! mpremote reset >/dev/null 2>&1; then
        sleep 1
        echo "trying again..."
        mpremote reset
    fi
    sleep 1
}

mpy_hard_reset_trap() {
    trap mpy_hard_reset EXIT INT TERM
}

mpy_soft_reset() {
    # mpremote can fail ungracefully if the board is in an invalid state
    # e.g. configured as a custom USB device
    if ! mpremote ls >/dev/null 2>&1; then
        echo "resetting..."
        sleep 1
        mpremote soft-reset
        sleep 1
    fi
}

mpy_repl() {
    mpremote # defaults to repl
}

cmd_setup() {
    echo "setting up python venv..."
    [ -d ".venv" ] || python3 -m venv .venv
    . .venv/bin/activate

    mkdir -p .mpy
    cd .mpy

    # install mpremote
    pip3 install "mpremote==$MICROPYTHON_VERSION"

    # download stubs
    pip3 install -U --target=stubs "micropython-$STUBS-stubs"

    # download micropython-lib (not used, just for reference)
    [ -d "micropython-lib" ] || git clone -c advice.detachedHead=false --depth 1 --branch "v$MICROPYTHON_VERSION" https://github.com/micropython/micropython-lib.git

    mkdir -p mip-sources
    cd mip-sources

    # download mip package sources
    for PKG in "${MIP_PACKAGES[@]}"; do
        echo "downloading '$PKG' source files..."
        NAME=${PKG%@*}
        VERSION=${PKG#*@}
        [ "$VERSION" == "$PKG" ] && VERSION=latest
        VERSION_JSON=$(curl -fsS "$MIP_INDEX/package/py/$NAME/$VERSION.json")
        NAMES=($(echo "$VERSION_JSON" | jq -r '.hashes[][0]'))
        HASHES=($(echo "$VERSION_JSON" | jq -r '.hashes[][1]'))
        for I in "${!NAMES[@]}"; do
            HASH=${HASHES[$I]}
            curl -#RL --create-dirs -o "${NAMES[$I]}" "$MIP_INDEX/file/${HASH:0:2}/$HASH"
        done
    done
}

cmd_reset() {
    setup_check
    mpy_hard_reset
}

cmd_clear() {
    setup_check
    mpy_hard_reset_trap
    mpy_soft_reset

    echo "deleting all device files..."
    mpremote fs --recursive rm / || true
}

cmd_push() {
    setup_check
    mpy_hard_reset_trap
    mpy_soft_reset

    if mpremote ls lib >/dev/null 2>&1; then
        echo "skipping installing mip packages"
    else
        echo "installing mip packages..."
        mpremote mip --index "$MIP_INDEX" install ${MIP_PACKAGES[@]}
    fi

    echo "copying files..."
    mpremote fs --recursive cp src/* :/
}

cmd_repl() {
    setup_check
    mpy_repl
}

case "${1:-}" in
    setup) cmd_setup ;;
    reset) cmd_reset ;;
    clear) cmd_clear ;;
    push) cmd_push ;;
    repl) cmd_repl ;;
    *) echo "usage: ${0##*/} {setup,reset,clear,push,repl}"
esac
