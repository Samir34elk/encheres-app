import Fastify from 'fastify';
import cors from '@fastify/cors';
import { salesRoutes } from './routes/sales.routes';

const PORT = parseInt(process.env.PORT || '3003', 10);
const HOST = process.env.HOST || '0.0.0.0';

const fastify = Fastify({
  logger: { level: process.env.LOG_LEVEL || 'info', transport: process.env.NODE_ENV !== 'production' ? { target: 'pino-pretty', options: { colorize: true, translateTime: 'HH:MM:ss Z', ignore: 'pid,hostname' } } : undefined }
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
    fastify.log.info(`Sales service listening on ${HOST}:${PORT}`);
  } catch (error) {
    fastify.log.error(error);
    process.exit(1);
  }
}

start();
