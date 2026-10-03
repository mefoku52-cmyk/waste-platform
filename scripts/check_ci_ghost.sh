#!/bin/bash
set -Eeuo pipefail
REPO="mefoku52-cmyk/waste-platform"
GHOST_ID=357626350
WF=$(gh api "/repos/$REPO/actions/workflows" \
     2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
for w in d.get('workflows',[]):
    if w['id']==$GHOST_ID:
        print(w.get('path','?'), w.get('state','?'))
")
if [ -n "$WF" ]; then
    echo "GHOST STILL ACTIVE: $WF"
    echo "Run support ticket: ~/cmep-p1-scratch/github_support_ticket.md"
    exit 1
else
    echo "GHOST GONE — push is safe"
    exit 0
fi
