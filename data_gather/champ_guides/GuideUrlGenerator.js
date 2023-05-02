const axios = require('axios');
const logger = require('./log_conf');

const RIOT_API_VERSIONS_URL = 'https://ddragon.leagueoflegends.com/api/versions.json';
const RIOT_API_CHAMPIONS_URL = 'http://ddragon.leagueoflegends.com/cdn/version/data/en_US/champion.json';
const MOBALYTICS_GUIDE_URL = 'https://app.mobalytics.gg/lol/champions/name/guide';

/**
 * A class to generate Mobalytics guide URLs for League of Legends champions.
 */
class GuideUrlGenerator {
  /**
   * Fetches the latest version of the Riot Data Dragon API.
   * @private
   * @returns {Promise<string>} The latest version of the Riot Data Dragon API.
   */
  async #getLatestVersion() {
    logger.info('Fetching latest version of Riot Data Dragon API');
    try {
      const response = await axios.get(RIOT_API_VERSIONS_URL);
      const versions = response.data;
      const latestVersion = versions[0];
      return latestVersion;
    } catch (error) {
      logger.error(`Error fetching latest version: ${error}`);
      throw error;
    }
  }

  /**
   * Gets all champion names from the Riot Data Dragon API and cleans the names.
   * @private
   * @returns {Promise<string[]>} An array of cleaned champion names.
   */
  async #getAllChampionNames() {
    logger.info('Fetching all champion names from Riot Data Dragon API');
    const latestVersion = await this.#getLatestVersion();
    try {
      const response = await axios.get(RIOT_API_CHAMPIONS_URL.replace('version', latestVersion));
      const champions = response.data.data;
      return Object.values(champions).map(champion => champion.name.replace(/[^\w\s]|_/g, "").replace(/\s+/g, ""));
    } catch (error) {
      logger.error(`Error fetching champion names: ${error}`);
      throw error;
    }
  }

  /**
   * Generates a list of Mobalytics guide URLs for every champion in League of Legends.
   * @public
   * @returns {Promise<string[]>} An array of Mobalytics guide URLs.
   */
  async generateChampionGuideUrls() {
    logger.info('Generating Mobalytics guide URLs for every champion');
    const championNames = await this.#getAllChampionNames();
    return championNames.map(championName => MOBALYTICS_GUIDE_URL.replace('name', championName));
  }
}

module.exports = GuideUrlGenerator;
