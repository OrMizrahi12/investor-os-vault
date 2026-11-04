#!/bin/sh
# Mac and Linux: find a Python that runs, then hand over to board.py. Usage: launch.sh start|stop|status|desktop
# On a problem it keeps the window open, so the words can be read.
here=$(cd "$(dirname "$0")" && pwd) || exit 1
python=
for try in "$here/../../.venv/bin/python" python3 python; do
    if "$try" -c 'import sys' >/dev/null 2>&1; then
        python=$try
        break
    fi
done
if [ -n "$python" ]; then
    PYTHONDONTWRITEBYTECODE=1 "$python" "$here/board.py" "$@"
    status=$?
else
    echo "The board needs Python 3.12 or newer, and none was found. Install one from https://www.python.org/downloads/ and start again."
    status=1
fi
if [ "$status" -ne 0 ] && [ -t 0 ]; then
    printf 'Press Enter to close this window. '
    read -r _
fi
exit "$status"
