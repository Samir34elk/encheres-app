import nodemailer from 'nodemailer';
import logger from '../../../shared/utils/logger';

export class EmailService {
  private transporter: nodemailer.Transporter;

  constructor() {
    // Create transporter (configure with your email provider)
    this.transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: parseInt(process.env.SMTP_PORT || '587'),
      secure: process.env.SMTP_SECURE === 'true',
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
      }
    });
  }

  async sendEmail(to: string, subject: string, html: string): Promise<void> {
    try {
      const info = await this.transporter.sendMail({
        from: process.env.SMTP_FROM || 'noreply@encheres.com',
        to,
        subject,
        html
      });

      logger.info(`Email sent: ${info.messageId}`);
    } catch (error: any) {
      logger.error(`Failed to send email: ${error.message}`);
      throw error;
    }
  }

  async sendWelcomeEmail(email: string, username: string): Promise<void> {
    const html = `
      <h1>Bienvenue sur Enchères du Domaine !</h1>
      <p>Bonjour ${username},</p>
      <p>Votre compte a été créé avec succès.</p>
      <p>Vous pouvez maintenant vous connecter et commencer à explorer les ventes aux enchères.</p>
      <br>
      <p>Cordialement,<br>L'équipe Enchères du Domaine</p>
    `;

    await this.sendEmail(email, 'Bienvenue sur Enchères du Domaine', html);
  }

  async sendAlertEmail(email: string, lots: any[]): Promise<void> {
    const lotsHtml = lots.map(lot => `
      <li>
        <strong>${lot.title}</strong><br>
        Prix: ${lot.currentPrice || 'N/A'} €<br>
        ${lot.description || ''}
      </li>
    `).join('');

    const html = `
      <h1>Nouveaux lots correspondant à vos alertes</h1>
      <p>Nous avons trouvé de nouveaux lots qui correspondent à vos critères de recherche:</p>
      <ul>
        ${lotsHtml}
      </ul>
      <p>Consultez notre site pour plus de détails.</p>
      <br>
      <p>Cordialement,<br>L'équipe Enchères du Domaine</p>
    `;

    await this.sendEmail(email, 'Nouveaux lots correspondant à vos alertes', html);
  }

  async sendPriceUpdateEmail(email: string, lot: any): Promise<void> {
    const html = `
      <h1>Mise à jour de prix</h1>
      <p>Le prix du lot suivant a été mis à jour:</p>
      <p>
        <strong>${lot.title}</strong><br>
        Nouveau prix: ${lot.currentPrice} €
      </p>
      <p>Consultez notre site pour plus de détails.</p>
      <br>
      <p>Cordialement,<br>L'équipe Enchères du Domaine</p>
    `;

    await this.sendEmail(email, 'Mise à jour de prix pour un lot favori', html);
  }
}

export default new EmailService();
