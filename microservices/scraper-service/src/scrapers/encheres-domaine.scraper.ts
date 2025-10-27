import puppeteer, { Browser, Page } from 'puppeteer';
import logger from '../../../shared/utils/logger';

export interface ScrapedSale {
  title: string;
  description?: string;
  saleDate?: string;
  location?: string;
  organizer?: string;
  sourceUrl: string;
  externalId?: string;
  lots: ScrapedLot[];
}

export interface ScrapedLot {
  title: string;
  description?: string;
  category?: string;
  startingPrice?: number;
  estimatedPrice?: number;
  lotNumber?: string;
  images?: string[];
}

export class EncheresDomaineScraper {
  private browser: Browser | null = null;
  private readonly BASE_URL = 'https://encheres-domaine.gouv.fr';

  async init(): Promise<void> {
    if (!this.browser) {
      this.browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
      });
      logger.info('Puppeteer browser initialized');
    }
  }

  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
      logger.info('Puppeteer browser closed');
    }
  }

  async scrapeSales(): Promise<ScrapedSale[]> {
    await this.init();

    const page = await this.browser!.newPage();
    const sales: ScrapedSale[] = [];

    try {
      logger.info(`Navigating to ${this.BASE_URL}/ventes`);
      await page.goto(`${this.BASE_URL}/ventes`, {
        waitUntil: 'networkidle2',
        timeout: 30000
      });

      // Extract sales list
      const salesData = await page.evaluate(() => {
        const salesElements = document.querySelectorAll('.sale-item, .vente-item, [class*="sale"], [class*="vente"]');
        const results: any[] = [];

        salesElements.forEach((element, index) => {
          const titleEl = element.querySelector('h2, h3, .title, [class*="title"]');
          const linkEl = element.querySelector('a');
          const dateEl = element.querySelector('.date, [class*="date"]');
          const locationEl = element.querySelector('.location, [class*="location"], [class*="lieu"]');

          if (titleEl || linkEl) {
            results.push({
              title: titleEl?.textContent?.trim() || `Vente ${index + 1}`,
              url: linkEl?.getAttribute('href'),
              date: dateEl?.textContent?.trim(),
              location: locationEl?.textContent?.trim()
            });
          }
        });

        return results;
      });

      logger.info(`Found ${salesData.length} sales`);

      // Scrape first 5 sales (to avoid overload)
      for (const saleData of salesData.slice(0, 5)) {
        try {
          const saleUrl = saleData.url?.startsWith('http')
            ? saleData.url
            : `${this.BASE_URL}${saleData.url}`;

          const sale: ScrapedSale = {
            title: saleData.title,
            saleDate: saleData.date,
            location: saleData.location,
            sourceUrl: saleUrl,
            externalId: saleData.url?.split('/').pop(),
            lots: []
          };

          // Scrape lots for this sale
          if (saleData.url) {
            const lots = await this.scrapeLots(page, saleUrl);
            sale.lots = lots;
          }

          sales.push(sale);
        } catch (error: any) {
          logger.error(`Error scraping sale: ${error.message}`);
        }
      }

    } catch (error: any) {
      logger.error(`Error scraping sales: ${error.message}`);
    } finally {
      await page.close();
    }

    return sales;
  }

  async scrapeLots(page: Page, saleUrl: string): Promise<ScrapedLot[]> {
    try {
      logger.info(`Scraping lots from ${saleUrl}`);
      await page.goto(saleUrl, {
        waitUntil: 'networkidle2',
        timeout: 30000
      });

      const lots = await page.evaluate(() => {
        const lotElements = document.querySelectorAll('.lot-item, [class*="lot"]');
        const results: any[] = [];

        lotElements.forEach((element, index) => {
          const titleEl = element.querySelector('h3, h4, .lot-title, [class*="title"]');
          const descEl = element.querySelector('.description, [class*="desc"]');
          const priceEl = element.querySelector('.price, [class*="price"], [class*="prix"]');
          const categoryEl = element.querySelector('.category, [class*="categor"]');
          const numberEl = element.querySelector('.lot-number, [class*="numero"]');
          const imgEl = element.querySelector('img');

          if (titleEl) {
            results.push({
              title: titleEl.textContent?.trim() || `Lot ${index + 1}`,
              description: descEl?.textContent?.trim(),
              category: categoryEl?.textContent?.trim(),
              lotNumber: numberEl?.textContent?.trim() || `${index + 1}`,
              priceText: priceEl?.textContent?.trim(),
              imageUrl: imgEl?.getAttribute('src')
            });
          }
        });

        return results;
      });

      logger.info(`Found ${lots.length} lots`);

      return lots.map((lot: any) => ({
        title: lot.title,
        description: lot.description,
        category: lot.category,
        lotNumber: lot.lotNumber,
        startingPrice: this.extractPrice(lot.priceText),
        estimatedPrice: this.extractPrice(lot.priceText),
        images: lot.imageUrl ? [lot.imageUrl] : []
      }));

    } catch (error: any) {
      logger.error(`Error scraping lots: ${error.message}`);
      return [];
    }
  }

  private extractPrice(priceText?: string): number | undefined {
    if (!priceText) return undefined;

    const match = priceText.match(/(\d+[\s,.]?\d*)/);
    if (match) {
      return parseFloat(match[1].replace(/[\s,]/g, ''));
    }

    return undefined;
  }
}

export default new EncheresDomaineScraper();
