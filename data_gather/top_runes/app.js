const puppeteer = require('puppeteer');
const kafka = require('kafka-node');
const RuneUrlGenerator = require('./rune_url_generator');
const logger = require('./log_conf');
const fs = require('fs');
const yaml = require('js-yaml');

const appConf = yaml.load(fs.readFileSync('app_conf.yml', 'utf8'));

const kafkaClient = new kafka.KafkaClient({ kafkaHost: appConf.kafka.bootstrap_servers });
const kafkaProducer = new kafka.Producer(kafkaClient);

/**
 * Extracts the text content of elements with a specified class from the given page.
 * 
 * @param {Object} page - Puppeteer's Page object representing the web page to extract the text content from.
 * @param {string} selector - The class name (or part of it) of the elements to extract the text content from.
 * @returns {Promise<string>} A Promise that resolves to the extracted text content joined with commas.
 * @throws Will throw an error if there's an issue with extracting the text content.
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
 * Scrapes specified URLs for rune data and champion names, then sends the extracted data to a Kafka topic.
 * 
 * @param {string[]} urls - An array of URLs to scrape for rune data and champion names.
 * @returns {Promise} A Promise that resolves when all messages are sent to Kafka or rejects if there's an issue with sending the messages.
 * @throws Will throw an error if there's an issue with scraping a URL.
 */
async function scrapeUrls(urls) {
    logger.info(`Scraping ${urls.length} URLs`);
    const browser = await puppeteer.launch({
        headless: "new"
    });
    const page = await browser.newPage();
    const sendPromises = [];

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
                  (err) => {
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
            throw err;
        }
    }
    await browser.close();
    return Promise.all(sendPromises);
}

(async () => {
  kafkaProducer.on('ready', async () => {
    const generator = new RuneUrlGenerator();
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

