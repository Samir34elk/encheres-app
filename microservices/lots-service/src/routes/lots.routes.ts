import { FastifyInstance } from 'fastify';
import lotsService from '../services/lots.service';
import { authMiddleware } from '../../../shared/middleware/auth';

export async function lotsRoutes(fastify: FastifyInstance) {
  // Get lots with filters and pagination
  fastify.get('/', async (request, reply) => {
    try {
      const { page = 1, size = 20, category, search, saleId, minPrice, maxPrice } = request.query as any;

      const result = await lotsService.getLots(
        parseInt(page),
        parseInt(size),
        category,
        search,
        saleId,
        minPrice ? parseFloat(minPrice) : undefined,
        maxPrice ? parseFloat(maxPrice) : undefined
      );

      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Get lot by ID
  fastify.get('/:id', async (request, reply) => {
    try {
      const { id } = request.params as any;
      const result = await lotsService.getLotById(id);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Create lot (admin only)
  fastify.post('/', {
    preHandler: authMiddleware({ requireAdmin: true })
  }, async (request, reply) => {
    try {
      const result = await lotsService.createLot(request.body);
      return reply.status(201).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Update lot (admin only)
  fastify.patch('/:id', {
    preHandler: authMiddleware({ requireAdmin: true })
  }, async (request, reply) => {
    try {
      const { id } = request.params as any;
      const result = await lotsService.updateLot(id, request.body);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Delete lot (admin only)
  fastify.delete('/:id', {
    preHandler: authMiddleware({ requireAdmin: true })
  }, async (request, reply) =>{
    try {
      const { id } = request.params as any;
      const result = await lotsService.deleteLot(id);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Favorites
  fastify.post('/:id/favorite', {
    preHandler: authMiddleware()
  }, async (request, reply) => {
    try {
      const { id } = request.params as any;
      const result = await lotsService.addFavorite(request.user!.userId, id);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  fastify.delete('/:id/favorite', {
    preHandler: authMiddleware()
  }, async (request, reply) => {
    try {
      const { id } = request.params as any;
      const result = await lotsService.removeFavorite(request.user!.userId, id);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  fastify.get('/favorites/me', {
    preHandler: authMiddleware()
  }, async (request, reply) => {
    try {
      const result = await lotsService.getFavorites(request.user!.userId);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Alerts
  fastify.post('/alerts', {
    preHandler: authMiddleware()
  }, async (request, reply) => {
    try {
      const result = await lotsService.createAlert(request.user!.userId, request.body);
      return reply.status(201).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  fastify.get('/alerts/me', {
    preHandler: authMiddleware()
  }, async (request, reply) => {
    try {
      const result = await lotsService.getAlerts(request.user!.userId);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  fastify.delete('/alerts/:alertId', {
    preHandler: authMiddleware()
  }, async (request, reply) => {
    try {
      const { alertId } = request.params as any;
      const result = await lotsService.deleteAlert(request.user!.userId, alertId);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });
}
