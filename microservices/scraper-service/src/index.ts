import Fastify from 'fastify';
import cors from '@fastify/cors';
import { scraperRoutes } from './routes/scraper.routes';
import { scheduleScrapingJob } from './queue/scraper.queue';

const PORT = parseInt(process.env.PORT || '3004', 10);
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
    await fastify.register(scraperRoutes, { prefix: '/api/v1/scraper' });

    // Health check
    fastify.get('/health', async () => {
      return { status: 'healthy', service: 'scraper-service' };
    });

    // Schedule scraping jobs
    await scheduleScrapingJob();

    // Start server
    await fastify.listen({ port: PORT, host: HOST });
    fastify.log.info(`Scraper service listening on ${HOST}:${PORT}`);
  } catch (error) {
    fastify.log.error(error);
    process.exit(1);
  }
}

start();
