const puppeteer = require('puppeteer');
const GuideUrlGenerator = require('./GuideUrlGenerator');
const logger = require('./Logger');

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
  

  
async function scrapeUrls(urls) {
    logger.info(`Scraping ${urls.length} URLs`);
    const browser = await puppeteer.launch({
        headless: "new"
    });
    const page = await browser.newPage();
    const results = [];

    for (const url of urls) {
        logger.info(`Scraping URL ${url}`);
        try {
        await page.goto(url, { waitUntil: 'networkidle2' });
        const textData = await extractTextFromElements(page, 'div.m-1tyqd9r');
        results.push({ url, textData });
        } catch (error) {
        console.error(`Error scraping URL ${url}:`, error);
        }
    }

    await browser.close();
    return results;
}

(async () => {
  const generator = new GuideUrlGenerator();
  const urls = await generator.generateChampionGuideUrls();
  const results = await scrapeUrls(urls);
  console.log(results);
})();


