import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcrypt';
import { generateToken } from '../../../shared/middleware/auth';
import { LoginRequest, RegisterRequest, User, JWTPayload, ApiResponse } from '../../../shared/types';
import { UnauthorizedError, ConflictError, ValidationError } from '../../../shared/utils/errors';

const prisma = new PrismaClient();
const SALT_ROUNDS = 10;

export class AuthService {
  async register(data: RegisterRequest): Promise<ApiResponse<{ user: User; token: string }>> {
    // Check if user already exists
    const existingUser = await prisma.user.findFirst({
      where: {
        OR: [
          { email: data.email },
          { username: data.username }
        ]
      }
    });

    if (existingUser) {
      throw new ConflictError('User with this email or username already exists');
    }

    // Validate password strength
    if (data.password.length < 8) {
      throw new ValidationError('Password must be at least 8 characters long');
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(data.password, SALT_ROUNDS);

    // Create user
    const user = await prisma.user.create({
      data: {
        email: data.email,
        username: data.username,
        password: hashedPassword,
        firstName: data.firstName,
        lastName: data.lastName
      }
    });

    // Generate JWT token
    const payload: JWTPayload = {
      userId: user.id,
      email: user.email,
      isAdmin: user.isAdmin
    };
    const token = generateToken(payload);

    // Create session
    await prisma.session.create({
      data: {
        userId: user.id,
        token,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
      }
    });

    // Remove password from response
    const { password: _, ...userWithoutPassword } = user;

    return {
      success: true,
      data: {
        user: userWithoutPassword as User,
        token
      }
    };
  }

  async login(data: LoginRequest): Promise<ApiResponse<{ user: User; token: string }>> {
    // Find user
    const user = await prisma.user.findUnique({
      where: { email: data.email }
    });

    if (!user) {
      throw new UnauthorizedError('Invalid email or password');
    }

    // Check if user is active
    if (!user.isActive) {
      throw new UnauthorizedError('Account is deactivated');
    }

    // Verify password
    const isPasswordValid = await bcrypt.compare(data.password, user.password);
    if (!isPasswordValid) {
      throw new UnauthorizedError('Invalid email or password');
    }

    // Generate JWT token
    const payload: JWTPayload = {
      userId: user.id,
      email: user.email,
      isAdmin: user.isAdmin
    };
    const token = generateToken(payload);

    // Create session
    await prisma.session.create({
      data: {
        userId: user.id,
        token,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
      }
    });

    // Remove password from response
    const { password: _, ...userWithoutPassword } = user;

    return {
      success: true,
      data: {
        user: userWithoutPassword as User,
        token
      }
    };
  }

  async logout(token: string): Promise<ApiResponse> {
    // Delete session
    await prisma.session.deleteMany({
      where: { token }
    });

    return {
      success: true,
      message: 'Logged out successfully'
    };
  }

  async getCurrentUser(userId: string): Promise<ApiResponse<User>> {
    const user = await prisma.user.findUnique({
      where: { id: userId }
    });

    if (!user) {
      throw new UnauthorizedError('User not found');
    }

    const { password: _, ...userWithoutPassword } = user;

    return {
      success: true,
      data: userWithoutPassword as User
    };
  }

  async updateProfile(userId: string, data: Partial<User>): Promise<ApiResponse<User>> {
    const user = await prisma.user.update({
      where: { id: userId },
      data: {
        firstName: data.firstName,
        lastName: data.lastName,
        username: data.username
      }
    });

    const { password: _, ...userWithoutPassword } = user;

    return {
      success: true,
      data: userWithoutPassword as User
    };
  }
}

export default new AuthService();
