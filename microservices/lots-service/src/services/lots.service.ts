import { PrismaClient } from '@prisma/client';
import { Lot, PaginatedResponse, ApiResponse, CreateLotRequest } from '../../../shared/types';
import { NotFoundError } from '../../../shared/utils/errors';

const prisma = new PrismaClient();

export class LotsService {
  async getLots(
    page: number = 1,
    size: number = 20,
    category?: string,
    search?: string,
    saleId?: string,
    minPrice?: number,
    maxPrice?: number
  ): Promise<ApiResponse<PaginatedResponse<Lot>>> {
    const skip = (page - 1) * size;

    const where: any = {};

    if (category) {
      where.category = category;
    }

    if (search) {
      where.OR = [
        { title: { contains: search, mode: 'insensitive' } },
        { description: { contains: search, mode: 'insensitive' } }
      ];
    }

    if (saleId) {
      where.saleId = saleId;
    }

    if (minPrice !== undefined || maxPrice !== undefined) {
      where.currentPrice = {};
      if (minPrice !== undefined) where.currentPrice.gte = minPrice;
      if (maxPrice !== undefined) where.currentPrice.lte = maxPrice;
    }

    const [lots, total] = await Promise.all([
      prisma.lot.findMany({
        where,
        skip,
        take: size,
        orderBy: { createdAt: 'desc' }
      }),
      prisma.lot.count({ where })
    ]);

    return {
      success: true,
      data: {
        items: lots as Lot[],
        total,
        page,
        size,
        pages: Math.ceil(total / size)
      }
    };
  }

  async getLotById(id: string): Promise<ApiResponse<Lot>> {
    const lot = await prisma.lot.findUnique({
      where: { id }
    });

    if (!lot) {
      throw new NotFoundError('Lot not found');
    }

    return {
      success: true,
      data: lot as Lot
    };
  }

  async createLot(data: CreateLotRequest): Promise<ApiResponse<Lot>> {
    const lot = await prisma.lot.create({
      data: {
        title: data.title,
        description: data.description,
        category: data.category,
        startingPrice: data.startingPrice,
        currentPrice: data.startingPrice,
        estimatedPrice: data.estimatedPrice,
        lotNumber: data.lotNumber,
        saleId: data.saleId
      }
    });

    return {
      success: true,
      data: lot as Lot
    };
  }

  async updateLot(id: string, data: Partial<Lot>): Promise<ApiResponse<Lot>> {
    const lot = await prisma.lot.update({
      where: { id },
      data: {
        title: data.title,
        description: data.description,
        category: data.category,
        currentPrice: data.currentPrice,
        estimatedPrice: data.estimatedPrice,
        images: data.images
      }
    });

    return {
      success: true,
      data: lot as Lot
    };
  }

  async deleteLot(id: string): Promise<ApiResponse> {
    await prisma.lot.delete({
      where: { id }
    });

    return {
      success: true,
      message: 'Lot deleted successfully'
    };
  }

  // Favorites
  async addFavorite(userId: string, lotId: string): Promise<ApiResponse> {
    await prisma.favorite.create({
      data: { userId, lotId }
    });

    return {
      success: true,
      message: 'Lot added to favorites'
    };
  }

  async removeFavorite(userId: string, lotId: string): Promise<ApiResponse> {
    await prisma.favorite.deleteMany({
      where: { userId, lotId }
    });

    return {
      success: true,
      message: 'Lot removed from favorites'
    };
  }

  async getFavorites(userId: string): Promise<ApiResponse<Lot[]>> {
    const favorites = await prisma.favorite.findMany({
      where: { userId },
      include: { lot: true }
    });

    const lots = favorites.map(f => f.lot);

    return {
      success: true,
      data: lots as Lot[]
    };
  }

  // Alerts
  async createAlert(userId: string, data: any): Promise<ApiResponse> {
    const alert = await prisma.alert.create({
      data: {
        userId,
        keywords: data.keywords,
        category: data.category,
        minPrice: data.minPrice,
        maxPrice: data.maxPrice
      }
    });

    return {
      success: true,
      data: alert
    };
  }

  async getAlerts(userId: string): Promise<ApiResponse> {
    const alerts = await prisma.alert.findMany({
      where: { userId, isActive: true }
    });

    return {
      success: true,
      data: alerts
    };
  }

  async deleteAlert(userId: string, alertId: string): Promise<ApiResponse> {
    await prisma.alert.deleteMany({
      where: { id: alertId, userId }
    });

    return {
      success: true,
      message: 'Alert deleted successfully'
    };
  }
}

export default new LotsService();
