#!/usr/bin/env tsx

/**
 * Monitoring script for Encheres microservices
 * Checks health of all services and reports status
 */

import axios from 'axios';

interface Service {
  name: string;
  url: string;
  healthPath: string;
}

const SERVICES: Service[] = [
  {
    name: 'API Gateway',
    url: process.env.API_GATEWAY_URL || 'https://encheres-api-gateway-v2.onrender.com',
    healthPath: '/health'
  },
  {
    name: 'Auth Service',
    url: process.env.AUTH_SERVICE_URL || 'https://encheres-auth-service-v2.onrender.com',
    healthPath: '/health'
  },
  {
    name: 'Lots Service',
    url: process.env.LOTS_SERVICE_URL || 'https://encheres-lots-service-v2.onrender.com',
    healthPath: '/health'
  },
  {
    name: 'Sales Service',
    url: process.env.SALES_SERVICE_URL || 'https://encheres-sales-service-v2.onrender.com',
    healthPath: '/health'
  },
  {
    name: 'Scraper Service',
    url: process.env.SCRAPER_SERVICE_URL || 'https://encheres-scraper-service-v2.onrender.com',
    healthPath: '/health'
  },
  {
    name: 'Notifications Service',
    url: process.env.NOTIFICATIONS_SERVICE_URL || 'https://encheres-notifications-service-v2.onrender.com',
    healthPath: '/health'
  }
];

interface HealthCheckResult {
  service: string;
  status: 'healthy' | 'unhealthy' | 'error';
  responseTime: number;
  error?: string;
  data?: any;
}

async function checkServiceHealth(service: Service): Promise<HealthCheckResult> {
  const start = Date.now();

  try {
    const response = await axios.get(`${service.url}${service.healthPath}`, {
      timeout: 10000,
      validateStatus: () => true // Don't throw on any status
    });

    const responseTime = Date.now() - start;

    if (response.status === 200) {
      return {
        service: service.name,
        status: 'healthy',
        responseTime,
        data: response.data
      };
    } else {
      return {
        service: service.name,
        status: 'unhealthy',
        responseTime,
        error: `HTTP ${response.status}`
      };
    }
  } catch (error: any) {
    const responseTime = Date.now() - start;
    return {
      service: service.name,
      status: 'error',
      responseTime,
      error: error.message
    };
  }
}

async function monitorServices() {
  console.log('\n🔍 Checking Encheres Microservices Health...\n');
  console.log('='.repeat(80));

  const results = await Promise.all(
    SERVICES.map(service => checkServiceHealth(service))
  );

  let healthyCount = 0;
  let unhealthyCount = 0;
  let errorCount = 0;

  for (const result of results) {
    const statusEmoji =
      result.status === 'healthy' ? '✅' :
      result.status === 'unhealthy' ? '⚠️' : '❌';

    console.log(`\n${statusEmoji} ${result.service}`);
    console.log(`   Status: ${result.status.toUpperCase()}`);
    console.log(`   Response Time: ${result.responseTime}ms`);

    if (result.error) {
      console.log(`   Error: ${result.error}`);
    }

    if (result.data) {
      console.log(`   Data: ${JSON.stringify(result.data)}`);
    }

    if (result.status === 'healthy') healthyCount++;
    else if (result.status === 'unhealthy') unhealthyCount++;
    else errorCount++;
  }

  console.log('\n' + '='.repeat(80));
  console.log(`\n📊 Summary:`);
  console.log(`   ✅ Healthy: ${healthyCount}/${SERVICES.length}`);
  console.log(`   ⚠️  Unhealthy: ${unhealthyCount}/${SERVICES.length}`);
  console.log(`   ❌ Errors: ${errorCount}/${SERVICES.length}`);

  const overallHealth = (healthyCount / SERVICES.length) * 100;
  console.log(`\n   Overall Health: ${overallHealth.toFixed(1)}%`);

  if (overallHealth === 100) {
    console.log('\n🎉 All services are healthy!\n');
  } else if (overallHealth >= 80) {
    console.log('\n⚠️  Some services are degraded\n');
  } else {
    console.log('\n❌ Critical: Multiple services are down\n');
  }

  return overallHealth;
}

// Run monitoring
monitorServices()
  .then((health) => {
    process.exit(health === 100 ? 0 : 1);
  })
  .catch((error) => {
    console.error('Monitoring failed:', error);
    process.exit(1);
  });
