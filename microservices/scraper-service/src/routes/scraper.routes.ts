import { FastifyInstance } from 'fastify';
import { scraperQueue } from '../queue/scraper.queue';
import { authMiddleware } from '../../../shared/middleware/auth';

export async function scraperRoutes(fastify: FastifyInstance) {
  // Trigger scraping manually (admin only)
  fastify.post('/trigger', {
    preHandler: authMiddleware({ requireAdmin: true })
  }, async (request, reply) => {
    try {
      const job = await scraperQueue.add('scrape-encheres', {});

      return reply.status(200).send({
        success: true,
        message: 'Scraping job triggered',
        jobId: job.id
      });
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Get scraping job status
  fastify.get('/status/:jobId', {
    preHandler: authMiddleware({ requireAdmin: true })
  }, async (request, reply) => {
    try {
      const { jobId } = request.params as any;
      const job = await scraperQueue.getJob(jobId);

      if (!job) {
        return reply.status(404).send({
          success: false,
          error: 'Job not found'
        });
      }

      const state = await job.getState();
      const progress = job.progress;

      return reply.status(200).send({
        success: true,
        data: {
          id: job.id,
          state,
          progress,
          returnValue: job.returnvalue
        }
      });
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Get recent scraping jobs
  fastify.get('/jobs', {
    preHandler: authMiddleware({ requireAdmin: true })
  }, async (request, reply) => {
    try {
      const completed = await scraperQueue.getCompleted(0, 10);
      const failed = await scraperQueue.getFailed(0, 10);
      const active = await scraperQueue.getActive();

      return reply.status(200).send({
        success: true,
        data: {
          active: active.map(j => ({ id: j.id, name: j.name, timestamp: j.timestamp })),
          completed: completed.map(j => ({ id: j.id, name: j.name, returnValue: j.returnvalue })),
          failed: failed.map(j => ({ id: j.id, name: j.name, failedReason: j.failedReason }))
        }
      });
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });
}
