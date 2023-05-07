const puppeteer = require('puppeteer');
const kafka = require('kafka-node');
const GuideUrlGenerator = require('./guide_url_generator');
const logger = require('./log_conf');
const fs = require('fs');
const yaml = require('js-yaml');

const appConf = yaml.load(fs.readFileSync('app_conf.yml', 'utf8'));

const kafkaClient = new kafka.KafkaClient({ kafkaHost: appConf.kafka.bootstrap_servers });
const kafkaProducer = new kafka.Producer(kafkaClient);

/**
 * Extracts the text content from elements on a given Puppeteer page based on the provided CSS selector.
 * @param {Object} page - A Puppeteer page object.
 * @param {string} selector - The partial CSS class to identify the target elements on the page.
 * @returns {Promise<string>} - A promise that resolves to the extracted text content joined by commas.
 */
async function extractTextFromElements(page, selector) {
  logger.info(`Extracting text from selector ${selector}`);
  try {
    const elements = await page.$$(`[class*='${selector}']`);
    const textData = await Promise.all(
      elements.map(async (element) => {
        return await page.evaluate((el) => el.textContent, element);
      })
    );
    return textData.join(', ');
  } catch (error) {
    logger.error(`Error extracting text from elements: ${error}`);
    throw error;
  }
}

/**
 * Scrapes the provided URLs using a headless Puppeteer browser instance, extracts text from the web pages, and sends the extracted text as messages to a Kafka topic.
 * @param {string[]} urls - An array of URLs to be scraped.
 * @returns {Promise<void>} - A promise that resolves when the scraping and message sending process is completed.
 */
async function scrapeUrls(urls) {
    logger.info(`Scraping ${urls.length} URLs`);
    const browser = await puppeteer.launch({
        headless: "new"
    });
    const page = await browser.newPage();
    const sendPromises = []; // Store promises for each Kafka message

    for (const url of urls) {
        logger.info(`Scraping URL ${url}`);
        try {
            await page.goto(url, { waitUntil: ['domcontentloaded', 'networkidle2'] });
            let runeData = await extractTextFromElements(page, 'Rune_title');
            let championName = url.split('/')[4];
            championName = championName.charAt(0).toUpperCase() + championName.slice(1);

            if (runeData !== "") {
              const sendPromise = new Promise((resolve, reject) => {
                kafkaProducer.send(
                  [
                    {
                      topic: appConf.kafka.topic,
                      messages: JSON.stringify({ champion: championName, runes: runeData}),
                    },
                  ],
                  (err, data) => {
                    if (err) {
                      logger.error(`Error sending message to Kafka: ${err}`);
                      reject(err);
                    } else {
                      logger.info(`Sent message to Kafka`);
                      resolve();
                    }
                  }
                );
              });
              sendPromises.push(sendPromise);
            } else {
              logger.error(`No text data found for URL ${url}`);
              continue;
            }

            
        } catch (err) {
            logger.error(`Error scraping URL ${url}: ${err}`);
        }
    }
    await browser.close();
    return Promise.all(sendPromises);
}

(async () => {
  kafkaProducer.on('ready', async () => {
    const generator = new GuideUrlGenerator();
    const urls = await generator.generateChampionRuneUrls();
    await scrapeUrls(urls);

    kafkaProducer.close(() => {
      logger.info('Kafka producer closed');
      process.exit();
    });
  });

  kafkaProducer.on('error', (err) => {
    logger.error('Error initializing Kafka producer:', err);
  });
})();

