#!/bin/bash
cd /home/dietpi/iran-osint-monitor
git add -A
if git diff --cached --quiet; then
    echo "No hay cambios"
else
    git commit -m "auto: datos $(date '+%Y-%m-%d %H:%M')"
    git push origin main
fi

# Rotar log si supera 5MB
LOG="/home/dietpi/iran-osint-monitor/pipeline_iran.log"
if [ -f "$LOG" ] && [ $(stat -c%s "$LOG") -gt 5242880 ]; then
    mv "$LOG" "${LOG}.bak"
    echo "Log rotado $(date)" > "$LOG"
fi
