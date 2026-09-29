#!/bin/bash
# Smart College AI Management Platform Startup Script

PORT=8080
cd "$(dirname "$0")"

echo "=========================================================="
echo "🎓 Starting Smart College AI — Digital Twin OS"
echo "👉 Local Web Portal: http://localhost:$PORT"
echo "🔗 Supabase Project URL: https://aqfqdjhddfvyprpwccyp.supabase.co"
echo "=========================================================="

python3 server.py $PORT
