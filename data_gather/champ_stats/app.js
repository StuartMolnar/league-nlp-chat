const puppeteer = require('puppeteer');
const kafka = require('kafka-node');
const logger = require('./log_conf');
const fs = require('fs');
const yaml = require('js-yaml');
const StatUrlGenerator = require('./stat_url_generator');

const appConf = yaml.load(fs.readFileSync('app_conf.yml', 'utf8'));

const kafkaClient = new kafka.KafkaClient({ kafkaHost: appConf.kafka.bootstrap_servers });
const kafkaProducer = new kafka.Producer(kafkaClient);
const kafkaConsumer = new kafka.Consumer(kafkaClient, [{ topic: appConf.kafka.topic }]);

/**
 * Extracts the text content of an element with a specified ID from the given page.
 * 
 * @param {Object} page - Puppeteer's Page object representing the web page to extract the text content from.
 * @param {string} selector - The ID of the element to extract the text content from.
 * @returns {Promise<string|null>} A Promise that resolves to the extracted text content or null if the element is not found.
 * @throws Will throw an error if there's an issue with extracting the text content.
 */
async function extractTextFromElements(page, selector) {
    console.log(`Extracting text from selector ${selector}`);
  
    try {
        const element = await page.$(`#${selector}`);
        if (!element) {
            console.log(`No element found with ID: ${selector}`);
            return null;
        }
        const textContent = await page.evaluate((el) => el.textContent, element);
        return textContent;
    } catch (error) {
        console.error(`Error extracting text from elements: ${error}`);
        throw error;
    }
}
  
/**
 * Scrapes specified URLs for win rates and champion names, then sends the extracted data to a Kafka topic.
 * 
 * @param {string[]} urls - An array of URLs to scrape for win rates and champion names.
 * @returns {Promise} A Promise that resolves when all messages are sent to Kafka or rejects if there's an issue with sending the messages.
 * @throws Will throw an error if there's an issue with scraping a URL.
 */
async function scrapeUrls(urls){
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
            let winrate = await extractTextFromElements(page, 'graphDD2');
            let championName = url.split('/')[5];
            championName = championName.charAt(0).toUpperCase() + championName.slice(1);

            if (winrate !== "") {
                const sendPromise = new Promise((resolve, reject) => {
                    kafkaProducer.send(
                        [
                            {
                                topic: appConf.kafka.topic,
                                messages: JSON.stringify({ champion: championName, winrate: winrate }),
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
        const generator = new StatUrlGenerator();
        const urls = await generator.generateChampionStatUrls();
        await scrapeUrls(urls);
        kafkaProducer.close(() => {
            logger.info('Kafka producer closed');
            process.exit();
        });
    });
    
    kafkaProducer.on('error', (err) => {
        logger.error('Error initializing Kafka producer:', err);
    });

    kafkaConsumer.on('message', (message) => {
        logger.info(message);
        logger.info(message.value);
    });

    kafkaConsumer.on('error', (err) => {
        logger.error('Error initializing Kafka consumer:', err);
    });
})();



