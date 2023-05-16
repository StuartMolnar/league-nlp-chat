const axios = require('axios');
const logger = require('./log_conf');

const RIOT_API_VERSIONS_URL = 'https://ddragon.leagueoflegends.com/api/versions.json';
const RIOT_API_CHAMPIONS_URL = 'http://ddragon.leagueoflegends.com/cdn/version/data/en_US/champion.json';
const STATS_URL = 'https://www.leagueofgraphs.com/champions/stats/name';

/**
 * A class to generate Mobalytics guide URLs for League of Legends champions.
 */
class StatUrlGenerator {
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

      // Map over the champion keys
      const championNames = Object.keys(champions).map(name => name.toLowerCase());

      return championNames;
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
  async generateChampionStatUrls() {
    logger.info('Generating leagueofgraphs champion stat URLs for every champion');
    const championNames = await this.#getAllChampionNames();
    return championNames.map(championName => STATS_URL.replace('name', championName));
  }
}

module.exports = StatUrlGenerator;

