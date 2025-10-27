import { FastifyInstance } from 'fastify';
import notificationService from '../services/notification.service';
import { authMiddleware } from '../../../shared/middleware/auth';

export async function notificationsRoutes(fastify: FastifyInstance) {
  // Get user notifications
  fastify.get('/me', {
    preHandler: authMiddleware
  }, async (request, reply) => {
    try {
      const result = await notificationService.getUserNotifications(request.user!.userId);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Send welcome notification (internal use)
  fastify.post('/welcome', async (request, reply) => {
    try {
      const { email, username } = request.body as any;
      await notificationService.sendWelcomeNotification(email, username);

      return reply.status(200).send({
        success: true,
        message: 'Welcome notification sent'
      });
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Send alert notification (internal use)
  fastify.post('/alert', async (request, reply) => {
    try {
      const { email, lots } = request.body as any;
      await notificationService.sendAlertNotification(email, lots);

      return reply.status(200).send({
        success: true,
        message: 'Alert notification sent'
      });
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });
}
