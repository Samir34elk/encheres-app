#!/bin/bash
# Script de test des builds Docker pour tous les microservices
# Auteur: Claude Code
# Date: 2025-10-27

set -e  # Exit on error

echo "🔧 Testing Microservices Docker Builds..."
echo "=========================================="
echo ""

cd "$(dirname "$0")"

SERVICES="auth-service lots-service sales-service notifications-service api-gateway"
FAILED_SERVICES=""
SUCCESS_COUNT=0
TOTAL_COUNT=0

for service in $SERVICES; do
  TOTAL_COUNT=$((TOTAL_COUNT + 1))
  echo ""
  echo "📦 Building $service..."
  echo "---"

  if docker build -t "encheres-$service-test" -f "$service/Dockerfile" . > "/tmp/docker-build-$service.log" 2>&1; then
    echo "✅ $service: BUILD SUCCESS"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  else
    echo "❌ $service: BUILD FAILED"
    echo "   Log: /tmp/docker-build-$service.log"
    FAILED_SERVICES="$FAILED_SERVICES $service"

    # Show last 20 lines of error log
    echo "   Last 20 lines of error:"
    tail -20 "/tmp/docker-build-$service.log" | sed 's/^/   /'
  fi
done

echo ""
echo "=========================================="
echo "📊 Build Summary:"
echo "   Success: $SUCCESS_COUNT / $TOTAL_COUNT"

if [ -n "$FAILED_SERVICES" ]; then
  echo "   Failed:$FAILED_SERVICES"
  echo ""
  echo "❌ Some builds failed. Check logs in /tmp/docker-build-*.log"
  exit 1
else
  echo ""
  echo "✅ All builds successful!"
  echo ""
  echo "🎉 Next steps:"
  echo "   1. Review the Docker images: docker images | grep encheres"
  echo "   2. Test a service locally: docker run -p 3001:3001 -e DATABASE_URL=... encheres-auth-service-test"
  echo "   3. Push to production: git push origin master"
fi
