import { PrismaClient } from '@prisma/client';
import { Sale, PaginatedResponse, ApiResponse, CreateSaleRequest } from '../../../shared/types';
import { NotFoundError } from '../../../shared/utils/errors';

const prisma = new PrismaClient();

export class SalesService {
  async getSales(
    page: number = 1,
    size: number = 20,
    status?: string,
    search?: string
  ): Promise<ApiResponse<PaginatedResponse<Sale>>> {
    const skip = (page - 1) * size;

    const where: any = {};

    if (status) {
      where.status = status;
    }

    if (search) {
      where.OR = [
        { title: { contains: search, mode: 'insensitive' } },
        { description: { contains: search, mode: 'insensitive' } },
        { location: { contains: search, mode: 'insensitive' } }
      ];
    }

    const [sales, total] = await Promise.all([
      prisma.sale.findMany({
        where,
        skip,
        take: size,
        orderBy: { saleDate: 'desc' }
      }),
      prisma.sale.count({ where })
    ]);

    return {
      success: true,
      data: {
        items: sales as Sale[],
        total,
        page,
        size,
        pages: Math.ceil(total / size)
      }
    };
  }

  async getSaleById(id: string): Promise<ApiResponse<Sale>> {
    const sale = await prisma.sale.findUnique({
      where: { id }
    });

    if (!sale) {
      throw new NotFoundError('Sale not found');
    }

    return {
      success: true,
      data: sale as Sale
    };
  }

  async createSale(data: CreateSaleRequest): Promise<ApiResponse<Sale>> {
    const sale = await prisma.sale.create({
      data: {
        title: data.title,
        description: data.description,
        saleDate: data.saleDate ? new Date(data.saleDate) : undefined,
        location: data.location,
        organizer: data.organizer,
        sourceUrl: data.sourceUrl
      }
    });

    return {
      success: true,
      data: sale as Sale
    };
  }

  async updateSale(id: string, data: Partial<Sale>): Promise<ApiResponse<Sale>> {
    const sale = await prisma.sale.update({
      where: { id },
      data: {
        title: data.title,
        description: data.description,
        saleDate: data.saleDate,
        location: data.location,
        organizer: data.organizer,
        status: data.status
      }
    });

    return {
      success: true,
      data: sale as Sale
    };
  }

  async deleteSale(id: string): Promise<ApiResponse> {
    await prisma.sale.delete({
      where: { id }
    });

    return {
      success: true,
      message: 'Sale deleted successfully'
    };
  }

  async getUpcomingSales(): Promise<ApiResponse<Sale[]>> {
    const sales = await prisma.sale.findMany({
      where: {
        status: 'upcoming',
        saleDate: {
          gte: new Date()
        }
      },
      orderBy: { saleDate: 'asc' },
      take: 10
    });

    return {
      success: true,
      data: sales as Sale[]
    };
  }
}

export default new SalesService();
