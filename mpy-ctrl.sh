#!/usr/bin/env bash

# MicroPython environment control utility.
# Author: Gonçalo MB <me@goncalomb.com>
# Version: 0.6
#
# I created this because I felt that the tooling around MicroPython
# was too disconnected and there was no standard way to configure a
# MicroPython project.
#
# See 'mpy-ctrl.conf' for example configuration.
#
# Features:
#
# - Setups a MicroPython environment with 'mpremote' and 'mpy-cross';
# - Downloads stubs;
# - Downloads dependencies (including mip packages);
# - Compiles the code to '.mpy';
# - Pushes the code to the device;
#
# Commands: setup, reset, clear, push, repl

set -euo pipefail
shopt -s extglob
cd -- "$(dirname -- "$0")"

[ ! -f "mpy-ctrl.conf" ] && echo "missing 'mpy-ctrl.conf'" && exit 1
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

mpy_build_vars() {
    if [ -n "${WRITE_BUILD_VARS:-}" ]; then
        mkdir -p .mpy/lib
        {
            echo "git_commit = \"$(git rev-parse HEAD 2>/dev/null)\""
            echo "git_version = \"$(git describe --tags --always --long --dirty 2>/dev/null)\""
            echo "args = $(jq -n --indent 4 --args '$ARGS.positional' -- "$@")"
        } >.mpy/lib/mpy_ctrl.py
    fi
}

mpy_cross_dir() {
    # note: boot.py and main.py cannot be compiled
    # compile .py to .mpy
    {
        cd -- "$1"
        find "." -type f -name "*.py" -and -not -path "./main.py" -and -not -path "./boot.py"
    } | while IFS= read -r F; do
        IN="$1/${F:2}"
        OUT="$2/${F:2:-3}.mpy"
        mkdir -p -- "$(dirname -- "$OUT")"
        mpy-cross -o "$OUT" "${COMPILE_MPY_ARGS[@]}" -- "$IN"
    done
    # copy non .py files
    {
        cd -- "$1"
        find "." -type f -not -name "*.py" -or -path "./main.py" -or -path "./boot.py"
    } | while IFS= read -r F; do
        IN="$1/${F:2}"
        OUT="$2/${F:2}"
        mkdir -p -- "$(dirname -- "$OUT")"
        cp -a "$IN" "$OUT"
    done
}

cmd_setup() {
    echo "setting up python venv..."
    [ -d ".venv" ] || python3 -m venv .venv
    . .venv/bin/activate

    mpy_build_vars

    mkdir -p .mpy
    cd .mpy

    # install mpremote and mpy-cross
    pip3 install \
        "mpremote==$MICROPYTHON_VERSION.*" \
        "mpy-cross==$MICROPYTHON_VERSION.*" \

    # download stubs
    pip3 install -U --target=stubs "micropython-$STUBS-stubs"

    # download micropython-lib (not used, just for reference)
    [ -d "micropython-lib" ] || git clone -c advice.detachedHead=false --depth 1 --branch "v$MICROPYTHON_VERSION" https://github.com/micropython/micropython-lib.git

    mkdir -p mip-sources

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
            FILE=mip-sources/${NAMES[$I]}
            curl -#RL --create-dirs -o "$FILE" "$MIP_INDEX/file/${HASH:0:2}/$HASH"
        done
    done

    # setup extra libs
    if command -v mpy_lib_setup >/dev/null; then
        echo "setting up extra libs..."
        mkdir -p lib lib-tmp
        (
            mpy_lib_git_clone() {
                DEST="lib-tmp/$1"
                [ -d "$DEST" ] || git clone -c advice.detachedHead=false --depth 1 --branch "$3" "$2" "$DEST"
            }
            mpy_lib_setup # call user function
        )
    fi
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
    mpy_build_vars "$@"
    mpy_hard_reset_trap
    mpy_soft_reset

    if mpremote ls lib >/dev/null 2>&1; then
        echo "skipping installing mip packages"
    elif [ "${#MIP_PACKAGES[@]}" -ne 0 ]; then
        echo "installing mip packages..."
        mpremote mip --index "$MIP_INDEX" install ${MIP_PACKAGES[@]}
    fi

    if [ -n "${COMPILE_MPY:-}" ]; then
        echo "compiling files..."
        # compile extra libs (.mpy/lib)
        if [ -d ".mpy/lib" ]; then
            mpy_cross_dir .mpy/lib .mpy/build/lib
        fi
        # compile src
        mpy_cross_dir src .mpy/build
        # copy built file
        echo "copying files..."
        mpremote fs --recursive cp .mpy/build/* :/
        return
    fi

    echo "copying files..."
    # copy extra libs (.mpy/lib)
    if [ -d ".mpy/lib" ]; then
        mpremote ls lib >/dev/null 2>&1 || mpremote mkdir lib # mkdir lib
        mpremote fs --recursive cp .mpy/lib/* :/lib/
    fi
    # copy src
    mpremote fs --recursive cp src/* :/
}

cmd_repl() {
    setup_check
    mpy_repl
}

CMD="${1:-}"
[ -z "$CMD" ] || shift
case "$CMD" in
    setup) cmd_setup ;;
    reset) cmd_reset ;;
    clear) cmd_clear ;;
    push) cmd_push "$@" ;;
    repl) cmd_repl ;;
    *) echo "usage: ${0##*/} {setup,reset,clear,push,repl} ..."
esac
