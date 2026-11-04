#!/bin/sh
# Double-click on a Mac. On Linux, use "Put on Desktop" once, then the launchers it writes.
exec sh "$(dirname "$0")/launch.sh" stop
