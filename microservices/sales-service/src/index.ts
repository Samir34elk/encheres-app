import Fastify from 'fastify';
import cors from '@fastify/cors';
import { salesRoutes } from './routes/sales.routes';
import logger from '../../shared/utils/logger';

const PORT = parseInt(process.env.PORT || '3003', 10);
const HOST = process.env.HOST || '0.0.0.0';

const fastify = Fastify({
  logger: logger
});

async function start() {
  try {
    // Register CORS
    await fastify.register(cors, {
      origin: process.env.CORS_ORIGIN || '*',
      credentials: true
    });

    // Register routes
    await fastify.register(salesRoutes, { prefix: '/api/v1/sales' });

    // Health check
    fastify.get('/health', async () => {
      return { status: 'healthy', service: 'sales-service' };
    });

    // Start server
    await fastify.listen({ port: PORT, host: HOST });
    logger.info(`Sales service listening on ${HOST}:${PORT}`);
  } catch (error) {
    logger.error(error);
    process.exit(1);
  }
}

start();
