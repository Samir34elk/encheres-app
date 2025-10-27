import { FastifyInstance } from 'fastify';
import authService from '../services/auth.service';
import { LoginRequest, RegisterRequest } from '../../../shared/types';
import { authMiddleware } from '../../../shared/middleware/auth';

export async function authRoutes(fastify: FastifyInstance) {
  // Register
  fastify.post<{ Body: RegisterRequest }>('/register', async (request, reply) => {
    try {
      const result = await authService.register(request.body);
      return reply.status(201).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Login
  fastify.post<{ Body: LoginRequest }>('/login', async (request, reply) => {
    try {
      const result = await authService.login(request.body);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Logout
  fastify.post('/logout', {
    preHandler: authMiddleware
  }, async (request, reply) => {
    try {
      const token = request.headers.authorization?.split(' ')[1] || '';
      const result = await authService.logout(token);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Get current user
  fastify.get('/me', {
    preHandler: authMiddleware
  }, async (request, reply) => {
    try {
      const result = await authService.getCurrentUser(request.user!.userId);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });

  // Update profile
  fastify.patch('/me', {
    preHandler: authMiddleware
  }, async (request, reply) => {
    try {
      const result = await authService.updateProfile(request.user!.userId, request.body);
      return reply.status(200).send(result);
    } catch (error: any) {
      return reply.status(error.statusCode || 500).send({
        success: false,
        error: error.message
      });
    }
  });
}
