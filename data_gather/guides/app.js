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
 * Extracts the text content of elements with a specified selector from the given page.
 * 
 * @param {Object} page - Puppeteer's Page object representing the web page to extract the text content from.
 * @param {string} selector - The CSS selector of the elements to extract the text content from.
 * @returns {Promise<string>} A Promise that resolves to the extracted text content joined with newlines.
 * @throws Will throw an error if there's an issue with extracting the text content.
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
 * Scrapes specified URLs for guide text data and champion names, then sends the extracted data to a Kafka topic.
 * 
 * @param {string[]} urls - An array of URLs to scrape for guide text data and champion names.
 * @returns {Promise} A Promise that resolves when all messages are sent to Kafka or rejects if there's an issue with sending the messages.
 * @throws Will throw an error if there's an issue with scraping a URL.
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
      await page.goto(url, { waitUntil: 'networkidle2' });
      let textData = await extractTextFromElements(page, 'div.m-1tyqd9r');
      if (textData === "") {
        logger.error(`No text data found for URL ${url}`);
        continue;
      }
      const championName = url.split('/')[5];

      // Wrap Kafka producer send call in a Promise
      const sendPromise = new Promise((resolve, reject) => {
        kafkaProducer.send(
          [
            {
              topic: appConf.kafka.topic,
              messages: JSON.stringify({ champion: championName, guide: textData }),
            },
          ],
          (err) => {
            if (err) {
              logger.error('Error producing message:', err);
              reject(err);
            } else {
              logger.info('Message sent to Kafka producer');
              resolve();
            }
          }
        );
      });

      sendPromises.push(sendPromise);
    } catch (err) {
      logger.error(`Error scraping URL ${url}:`, err);
      throw err;
    }
  }

  await browser.close();
  return Promise.all(sendPromises);
}


(async () => {
  kafkaProducer.on('ready', async () => {
    const generator = new GuideUrlGenerator();
    const urls = await generator.generateChampionGuideUrls();
    await scrapeUrls(urls);

    kafkaClient.close(() => {
      logger.info('Kafka producer closed');
      process.exit(0);
    });
  });

  kafkaProducer.on('error', (err) => {
    logger.error('Error initializing Kafka producer:', err);
  });
})();

