import Fastify from 'fastify';
import cors from '@fastify/cors';
import proxy from '@fastify/http-proxy';
import rateLimit from '@fastify/rate-limit';

const PORT = parseInt(process.env.PORT || '3000', 10);
const HOST = process.env.HOST || '0.0.0.0';

// Service URLs (from environment or default for local dev)
const AUTH_SERVICE = process.env.AUTH_SERVICE_URL || 'http://localhost:3001';
const LOTS_SERVICE = process.env.LOTS_SERVICE_URL || 'http://localhost:3002';
const SALES_SERVICE = process.env.SALES_SERVICE_URL || 'http://localhost:3003';
const SCRAPER_SERVICE = process.env.SCRAPER_SERVICE_URL || 'http://localhost:3004';
const NOTIFICATIONS_SERVICE = process.env.NOTIFICATIONS_SERVICE_URL || 'http://localhost:3005';

const fastify = Fastify({
  logger: { level: process.env.LOG_LEVEL || 'info', transport: process.env.NODE_ENV !== 'production' ? { target: 'pino-pretty', options: { colorize: true, translateTime: 'HH:MM:ss Z', ignore: 'pid,hostname' } } : undefined },
  trustProxy: true
});

async function start() {
  try {
    // Register CORS
    await fastify.register(cors, {
      origin: process.env.CORS_ORIGIN?.split(',') || ['http://localhost:5173', 'http://localhost:3000'],
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
      allowedHeaders: ['Authorization', 'Content-Type', 'Accept']
    });

    // Register rate limiting
    await fastify.register(rateLimit, {
      max: 100, // Max 100 requests
      timeWindow: '1 minute'
    });

    // Health check
    fastify.get('/health', async () => {
      return {
        status: 'healthy',
        service: 'api-gateway',
        timestamp: new Date().toISOString()
      };
    });

    // Root endpoint
    fastify.get('/', async () => {
      return {
        name: 'Enchères du Domaine API Gateway',
        version: '1.0.0',
        services: {
          auth: `${AUTH_SERVICE}/health`,
          lots: `${LOTS_SERVICE}/health`,
          sales: `${SALES_SERVICE}/health`,
          scraper: `${SCRAPER_SERVICE}/health`,
          notifications: `${NOTIFICATIONS_SERVICE}/health`
        }
      };
    });

    // Proxy routes to microservices

    // Auth service
    await fastify.register(proxy, {
      upstream: AUTH_SERVICE,
      prefix: '/api/v1/auth',
      rewritePrefix: '/api/v1/auth',
      http2: false
    });

    // Lots service
    await fastify.register(proxy, {
      upstream: LOTS_SERVICE,
      prefix: '/api/v1/lots',
      rewritePrefix: '/api/v1/lots',
      http2: false
    });

    // Sales service
    await fastify.register(proxy, {
      upstream: SALES_SERVICE,
      prefix: '/api/v1/sales',
      rewritePrefix: '/api/v1/sales',
      http2: false
    });

    // Scraper service (admin only routes)
    await fastify.register(proxy, {
      upstream: SCRAPER_SERVICE,
      prefix: '/api/v1/scraper',
      rewritePrefix: '/api/v1/scraper',
      http2: false
    });

    // Notifications service
    await fastify.register(proxy, {
      upstream: NOTIFICATIONS_SERVICE,
      prefix: '/api/v1/notifications',
      rewritePrefix: '/api/v1/notifications',
      http2: false
    });

    // Start server
    await fastify.listen({ port: PORT, host: HOST });
    fastify.log.info(`API Gateway listening on ${HOST}:${PORT}`);
    fastify.log.info('Service routes:');
    fastify.log.info(`  Auth: ${AUTH_SERVICE}`);
    fastify.log.info(`  Lots: ${LOTS_SERVICE}`);
    fastify.log.info(`  Sales: ${SALES_SERVICE}`);
    fastify.log.info(`  Scraper: ${SCRAPER_SERVICE}`);
    fastify.log.info(`  Notifications: ${NOTIFICATIONS_SERVICE}`);
  } catch (error) {
    fastify.log.error(error);
    process.exit(1);
  }
}

start();
