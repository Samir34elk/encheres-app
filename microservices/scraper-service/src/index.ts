import Fastify from 'fastify';
import cors from '@fastify/cors';
import { scraperRoutes } from './routes/scraper.routes';
import { scheduleScrapingJob } from './queue/scraper.queue';
import logger from '../../shared/utils/logger';

const PORT = parseInt(process.env.PORT || '3004', 10);
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
    await fastify.register(scraperRoutes, { prefix: '/api/v1/scraper' });

    // Health check
    fastify.get('/health', async () => {
      return { status: 'healthy', service: 'scraper-service' };
    });

    // Schedule scraping jobs
    await scheduleScrapingJob();

    // Start server
    await fastify.listen({ port: PORT, host: HOST });
    logger.info(`Scraper service listening on ${HOST}:${PORT}`);
  } catch (error) {
    logger.error(error);
    process.exit(1);
  }
}

start();
