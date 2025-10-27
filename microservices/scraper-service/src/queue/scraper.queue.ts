import { Queue, Worker, Job } from 'bullmq';
import { PrismaClient } from '@prisma/client';
import encheresScraper, { ScrapedSale } from '../scrapers/encheres-domaine.scraper';
import logger from '../../../shared/utils/logger';
import axios from 'axios';

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const SALES_SERVICE_URL = process.env.SALES_SERVICE_URL || 'http://localhost:3003';
const LOTS_SERVICE_URL = process.env.LOTS_SERVICE_URL || 'http://localhost:3002';

const prisma = new PrismaClient();

// Create queue
export const scraperQueue = new Queue('scraper', {
  connection: {
    url: REDIS_URL
  }
});

// Worker to process scraping jobs
export const scraperWorker = new Worker(
  'scraper',
  async (job: Job) => {
    logger.info(`Processing scraping job ${job.id}`);

    try {
      // Scrape sales and lots
      const scrapedSales = await encheresScraper.scrapeSales();
      logger.info(`Scraped ${scrapedSales.length} sales`);

      let savedSales = 0;
      let savedLots = 0;

      // Save each sale and its lots
      for (const scrapedSale of scrapedSales) {
        try {
          // Create sale via sales-service
          const saleResponse = await axios.post(`${SALES_SERVICE_URL}/api/v1/sales`, {
            title: scrapedSale.title,
            description: scrapedSale.description,
            saleDate: scrapedSale.saleDate,
            location: scrapedSale.location,
            organizer: scrapedSale.organizer,
            sourceUrl: scrapedSale.sourceUrl
          });

          const sale = saleResponse.data.data;
          savedSales++;
          logger.info(`Saved sale: ${sale.title}`);

          // Create lots via lots-service
          for (const lot of scrapedSale.lots) {
            try {
              await axios.post(`${LOTS_SERVICE_URL}/api/v1/lots`, {
                ...lot,
                saleId: sale.id
              });
              savedLots++;
            } catch (error: any) {
              logger.error(`Error saving lot: ${error.message}`);
            }
          }

        } catch (error: any) {
          logger.error(`Error saving sale: ${error.message}`);
        }
      }

      logger.info(`Scraping complete: ${savedSales} sales, ${savedLots} lots saved`);

      return {
        success: true,
        salesScraped: scrapedSales.length,
        salesSaved: savedSales,
        lotsSaved: savedLots
      };

    } catch (error: any) {
      logger.error(`Scraping job failed: ${error.message}`);
      throw error;
    }
  },
  {
    connection: {
      url: REDIS_URL
    }
  }
);

// Schedule scraping job every 6 hours
export async function scheduleScrapingJob() {
  await scraperQueue.add(
    'scrape-encheres',
    {},
    {
      repeat: {
        pattern: '0 */6 * * *' // Every 6 hours
      }
    }
  );
  logger.info('Scheduled scraping job to run every 6 hours');
}
