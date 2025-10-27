import { FastifyInstance } from 'fastify';
import salesService from '../services/sales.service';
import { authMiddleware } from '../../../shared/middleware/auth';

export async function salesRoutes(fastify: FastifyInstance) {
  // Get sales with filters and pagination
  fastify.get('/', async (request, reply) => {
    try {
      const { page = 1, size = 20, status, search } = request.query as any;

      const result = await salesService.getSales(
        parseInt(page),
        parseInt(size),
        status,
        search
      );

      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Get upcoming sales
  fastify.get('/upcoming', async (request, reply) => {
    try {
      const result = await salesService.getUpcomingSales();
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Get sale by ID
  fastify.get('/:id', async (request, reply) => {
    try {
      const { id } = request.params as any;
      const result = await salesService.getSaleById(id);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Create sale (admin only)
  fastify.post('/', {
    preHandler: (req, rep) => authMiddleware(req, rep, { requireAdmin: true })
  }, async (request, reply) => {
    try {
      const result = await salesService.createSale(request.body);
      return reply.status(201).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Update sale (admin only)
  fastify.patch('/:id', {
    preHandler: (req, rep) => authMiddleware(req, rep, { requireAdmin: true })
  }, async (request, reply) => {
    try {
      const { id } = request.params as any;
      const result = await salesService.updateSale(id, request.body);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Delete sale (admin only)
  fastify.delete('/:id', {
    preHandler: (req, rep) => authMiddleware(req, rep, { requireAdmin: true })
  }, async (request, reply) => {
    try {
      const { id } = request.params as any;
      const result = await salesService.deleteSale(id);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });
}
