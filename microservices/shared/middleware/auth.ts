import { FastifyRequest, FastifyReply } from 'fastify';
import jwt from 'jsonwebtoken';
import { JWTPayload } from '../types';

// Extend Fastify request type to include user
declare module 'fastify' {
  interface FastifyRequest {
    user?: JWTPayload;
  }
}

export const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production';
export const JWT_EXPIRES_IN = '7d';

export interface AuthMiddlewareOptions {
  requireAuth?: boolean;
  requireAdmin?: boolean;
}

export function authMiddleware(options: AuthMiddlewareOptions = { requireAuth: true }) {
  return async (request: FastifyRequest, reply: FastifyReply) => {
    const { requireAuth = true, requireAdmin = false } = options;

    const authHeader = request.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      if (requireAuth) {
        return reply.status(401).send({
          success: false,
          error: 'No authorization token provided'
        });
      }
      return;
    }

    const token = authHeader.substring(7);

    try {
      const decoded = jwt.verify(token, JWT_SECRET) as JWTPayload;
      request.user = decoded;

      if (requireAdmin && !decoded.isAdmin) {
        return reply.status(403).send({
          success: false,
          error: 'Admin access required'
        });
      }
    } catch (error) {
      if (requireAuth) {
        return reply.status(401).send({
          success: false,
          error: 'Invalid or expired token'
        });
      }
    }
  };
}

export function generateToken(payload: JWTPayload): string {
  return jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });
}

export function verifyToken(token: string): JWTPayload | null {
  try {
    return jwt.verify(token, JWT_SECRET) as JWTPayload;
  } catch (error) {
    return null;
  }
}
