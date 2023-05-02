const puppeteer = require('puppeteer');
const kafka = require('kafka-node');
const GuideUrlGenerator = require('./GuideUrlGenerator');
const logger = require('./log_conf');
const fs = require('fs');
const yaml = require('js-yaml');

const appConf = yaml.load(fs.readFileSync('app_conf.yml', 'utf8'));

const kafkaClient = new kafka.KafkaClient({ kafkaHost: appConf.kafka.bootstrap_servers });
const kafkaProducer = new kafka.Producer(kafkaClient);

/**
 * Extracts the text content from elements on a given Puppeteer page based on the provided CSS selector.
 * @param {Object} page - A Puppeteer page object.
 * @param {string} selector - The CSS selector to identify the target elements on the page.
 * @returns {Promise<string>} - A promise that resolves to the extracted text content joined by newlines.
 */
async function extractTextFromElements(page, selector) {
    logger.info(`Extracting text from selector ${selector}`);
    const elements = await page.$$(selector);
    const textData = [];
  
    for (const element of elements) {
      const pTags = await element.$$('p');
      const elementText = [];
  
      for (const pTag of pTags.slice(0, -1)) {
        const textContent = await pTag.evaluate(node => node.textContent.trim());
        elementText.push(textContent);
      }
  
      textData.push(elementText.join('\n'));
    };
    return textData.join('\n');
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

    for (const url of urls) {
        logger.info(`Scraping URL ${url}`);
        try {
        await page.goto(url, { waitUntil: 'networkidle2' });
        const textData = await extractTextFromElements(page, 'div.m-1tyqd9r');
        kafkaProducer.send(
          [
            {
              topic: appConf.kafka.topic,
              messages: JSON.stringify(textData),
            },
          ],
          (err) => {
            if (err) {
              logger.error('Error producing message:', err);
            } else {
              logger.info('Message sent to Kafka producer');
            }
          }
        );
        } catch (error) {
          logger.error(`Error scraping URL ${url}:`, error);
        }
    }

    await browser.close();
}

(async () => {
  kafkaProducer.on('ready', async () => {
    const generator = new GuideUrlGenerator();
    const urls = await generator.generateChampionGuideUrls();
    await scrapeUrls(urls);
  });

  kafkaProducer.on('error', (err) => {
    logger.error('Error initializing Kafka producer:', err);
  });
})();

