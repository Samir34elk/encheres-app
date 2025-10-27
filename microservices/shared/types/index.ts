// Shared TypeScript types across all microservices

export interface User {
  id: string;
  email: string;
  username: string;
  firstName?: string;
  lastName?: string;
  isActive: boolean;
  isAdmin: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface JWTPayload {
  userId: string;
  email: string;
  isAdmin: boolean;
}

export interface Lot {
  id: string;
  title: string;
  description?: string;
  category?: string;
  startingPrice?: number;
  currentPrice?: number;
  estimatedPrice?: number;
  lotNumber?: string;
  images?: string[];
  saleId: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Sale {
  id: string;
  title: string;
  description?: string;
  saleDate?: Date;
  location?: string;
  organizer?: string;
  status: 'upcoming' | 'ongoing' | 'completed' | 'cancelled';
  sourceUrl?: string;
  externalId?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Favorite {
  id: string;
  userId: string;
  lotId: string;
  createdAt: Date;
}

export interface Alert {
  id: string;
  userId: string;
  keywords?: string;
  category?: string;
  minPrice?: number;
  maxPrice?: number;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface Notification {
  id: string;
  userId: string;
  type: 'email' | 'push';
  subject: string;
  message: string;
  sentAt?: Date;
  status: 'pending' | 'sent' | 'failed';
  createdAt: Date;
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Request types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

export interface CreateLotRequest {
  title: string;
  description?: string;
  category?: string;
  startingPrice?: number;
  estimatedPrice?: number;
  lotNumber?: string;
  saleId: string;
}

export interface CreateSaleRequest {
  title: string;
  description?: string;
  saleDate?: string;
  location?: string;
  organizer?: string;
  sourceUrl?: string;
}

export interface CreateAlertRequest {
  keywords?: string;
  category?: string;
  minPrice?: number;
  maxPrice?: number;
}
