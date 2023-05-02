const axios = require('axios');

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
    try {
      const response = await axios.get('https://ddragon.leagueoflegends.com/api/versions.json');
      const versions = response.data;
      const latestVersion = versions[0];
      return latestVersion;
    } catch (error) {
      console.error(`Error fetching latest version: ${error}`);
    }
  }

  /**
   * Gets all champion names from the Riot Data Dragon API and cleans the names.
   * @private
   * @returns {Promise<string[]>} An array of cleaned champion names.
   */
  async #getAllChampionNames() {
    const latestVersion = await this.#getLatestVersion();
    try {
      const response = await axios.get(`http://ddragon.leagueoflegends.com/cdn/${latestVersion}/data/en_US/champion.json`);
      const champions = response.data.data;
      let championNames = [];
      for (let champion in champions) {
        let championName = champions[champion].name;
        championName = championName.replace(/[^\w\s]|_/g, "").replace(/\s+/g, "");
        championNames.push(championName);
      }
      return championNames;
    } catch (error) {
      console.error(`Error fetching champion names: ${error}`);
    }
  }

  /**
   * Generates a list of Mobalytics guide URLs for every champion in League of Legends.
   * @public
   * @returns {Promise<string[]>} An array of Mobalytics guide URLs.
   */
  async generateChampionGuideUrls() {
    const championNames = await this.#getAllChampionNames();
    const baseUrl = 'https://app.mobalytics.gg/lol/champions/name/guide';
    let championGuideUrls = [];
    championNames.forEach(championName => {
      let championGuideUrl = baseUrl.replace('name', championName);
      championGuideUrls.push(championGuideUrl);
    });
    return championGuideUrls;
  }
}

module.exports = GuideUrlGenerator;
