import { PrismaClient } from '@prisma/client';
import { ApiResponse } from '../../../shared/types';
import emailService from './email.service';
import logger from '../../../shared/utils/logger';

const prisma = new PrismaClient();

export class NotificationService {
  async createNotification(
    userId: string,
    type: string,
    subject: string,
    message: string
  ): Promise<ApiResponse> {
    const notification = await prisma.notification.create({
      data: {
        userId,
        type,
        subject,
        message,
        status: 'pending'
      }
    });

    return {
      success: true,
      data: notification
    };
  }

  async sendNotification(notificationId: string, userEmail: string): Promise<ApiResponse> {
    const notification = await prisma.notification.findUnique({
      where: { id: notificationId }
    });

    if (!notification) {
      return {
        success: false,
        error: 'Notification not found'
      };
    }

    try {
      // Send email
      await emailService.sendEmail(userEmail, notification.subject, notification.message);

      // Update notification status
      await prisma.notification.update({
        where: { id: notificationId },
        data: {
          status: 'sent',
          sentAt: new Date()
        }
      });

      return {
        success: true,
        message: 'Notification sent successfully'
      };

    } catch (error: any) {
      logger.error(`Failed to send notification: ${error.message}`);

      // Update notification status to failed
      await prisma.notification.update({
        where: { id: notificationId },
        data: {
          status: 'failed'
        }
      });

      return {
        success: false,
        error: error.message
      };
    }
  }

  async getUserNotifications(userId: string): Promise<ApiResponse> {
    const notifications = await prisma.notification.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
      take: 50
    });

    return {
      success: true,
      data: notifications
    };
  }

  async sendWelcomeNotification(email: string, username: string): Promise<void> {
    try {
      await emailService.sendWelcomeEmail(email, username);
      logger.info(`Welcome email sent to ${email}`);
    } catch (error: any) {
      logger.error(`Failed to send welcome email: ${error.message}`);
    }
  }

  async sendAlertNotification(email: string, lots: any[]): Promise<void> {
    try {
      await emailService.sendAlertEmail(email, lots);
      logger.info(`Alert email sent to ${email}`);
    } catch (error: any) {
      logger.error(`Failed to send alert email: ${error.message}`);
    }
  }
}

export default new NotificationService();
