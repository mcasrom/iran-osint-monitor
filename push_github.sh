#!/bin/bash
cd /home/dietpi/iran-osint-monitor
git add -A
if git diff --cached --quiet; then
    echo "No hay cambios"
else
    git commit -m "auto: datos $(date '+%Y-%m-%d %H:%M')"
    git push origin main
fi
