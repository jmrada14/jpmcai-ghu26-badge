#!/bin/sh
# Give jpm_payments_ai its payment card icon and tap animation in the badge's
# menu. The menu ignores icon.png: it draws tiles from icons.mpy, so this
# patches the menu's src/icons.py, rebuilds icons.mpy and adds the animation.
# Needs Python 3 and network access once (to install mpy-cross 1.26.1, the
# version that reproduces the badge's own icons.mpy byte for byte).
#
# Usage: tools/install_icon.sh [/Volumes/BADGER]
set -eu

VOLUME="${1:-/Volumes/BADGER}"
MENU="$VOLUME/apps/menu"
HERE="$(cd "$(dirname "$0")" && pwd)"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/jpm-payments-ai"
BACKUP="$CACHE/menu-backup"

[ -f "$MENU/src/icons.py" ] && [ -f "$MENU/icons.mpy" ] && [ -d "$MENU/anim" ] \
    || { echo "Menu not found at $MENU (open Mass Storage on the badge first)" >&2; exit 1; }
mkdir -p "$CACHE"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [ ! -f "$BACKUP/icons.mpy" ]; then
    mkdir -p "$BACKUP" && cp "$MENU/icons.mpy" "$MENU/src/icons.py" "$BACKUP/"
fi
if [ ! -x "$CACHE/venv/bin/mpy-cross" ]; then
    python3 -m venv "$CACHE/venv"
    "$CACHE/venv/bin/pip" install -q --disable-pip-version-check mpy-cross==1.26.1.post2
fi

# menu_icon.py replaces only this app's entry; other apps' icons are kept
python3 -I "$HERE/menu_icon.py" --icons-src "$MENU/src/icons.py" --icons-out "$WORK/icons.py" \
    --anim-out "$WORK/jpm_payments_ai.bin"
(cd "$WORK" && "$CACHE/venv/bin/mpy-cross" icons.py -o icons.mpy)  # relative name, like the stock build
# animation first, then the source, then the compiled icons the menu loads
for pair in "jpm_payments_ai.bin anim/jpm_payments_ai.bin" "icons.py src/icons.py" "icons.mpy icons.mpy"; do
    from="${pair% *}"; to="${pair#* }"
    COPYFILE_DISABLE=1 cp "$WORK/$from" "$MENU/$to"
    cmp -s "$WORK/$from" "$MENU/$to" || { echo "Copy of $to didn't verify" >&2; exit 1; }
done
rm -f "$MENU"/._* "$MENU"/src/._* "$MENU"/anim/._*
sync
echo "Payment card icon installed. The menu's originals are backed up in $BACKUP"
