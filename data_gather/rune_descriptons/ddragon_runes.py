import requests
import json
import tarfile
import os
import shutil
from io import BytesIO
import re

import logging
import logging.config
import yaml
from kafka import KafkaProducer

DDRAGON_FILE = "ddragon-data-"

# Initialize the Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Load the configuration files
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


class DDragonRunes:
    """
    A class used to fetch and process the latest rune data from DDragon,
    clean the data, and produce it to a Kafka topic.

    Attributes:
        version (str): The latest version of DDragon.
        rune_data (list): A list of cleaned rune data after processing.

    Methods:
        produce_rune_data: Downloads and processes the latest rune data and sends it to a Kafka topic.

    Usage:
        ddragon_runes = DDragonRunes()
        
        ddragon_runes.produce_rune_data(topic)
    """
    def __init__(self):
        """
        Initializes a DDragonRunes object.

        Fetches the latest DDragon version from the official API and initializes
        the rune_data attribute as an empty list.

        Call the produce_rune_data method to download, process, and send rune data to a Kafka topic.
        """
        logger.info("DDragonRunes object initialized")
        self.version = self.__get_latest_version()
        self.rune_data = []
        

    def __get_latest_version(self):
        """
        Fetches the latest version of DDragon from the official API.

        Returns:
            str: The latest version of DDragon.
        """
        logger.info("Getting latest version of DDragon")
        ddragon_version_url = "https://ddragon.leagueoflegends.com/api/versions.json"

        response = requests.get(ddragon_version_url)
        versions = json.loads(response.text)
        return versions[0]
    
    def __clean_up(self, version):
        """
        Removes the downloaded DDragon assets.
        """
        logger.info("Cleaning up ddragon data assets")
        shutil.rmtree(f"ddragon-data-{version}")
    
    def __is_newer_version(self):
        """
        Compares the latest version of DDragon with the version in the current data file.

        Returns:
            bool: True if the latest version is newer than the version in the file, False otherwise.
        """
        logger.info("Checking if there is a newer version of DDragon")

        # Look for a file named "ddragon-data-{version}" in the current directory
        current_version_file = None
        for file in os.listdir():
            if file.startswith(DDRAGON_FILE):
                current_version_file = file
                break

        if current_version_file is None:
            logger.warning("No ddragon-data file found")
            return True

        # Extract the version number from the file name
        current_version = current_version_file.replace(DDRAGON_FILE, "")

        # Compare the version number from the file name to the latest version
        if self.version > current_version:
            logger.info("Version is newer than the one in the file")
            self.__clean_up(current_version)
            return True
        
        logger.info("Version is equal to or older than the one in the file")
        return False


    def __download_and_extract_ddragon(self):
        """
        Downloads and extracts the latest DDragon data if the version is newer than the one in the file.
        The data is extracted to a folder named "ddragon-data-{version}".
        """
        if self.__is_newer_version():
            logger.info("Downloading and extracting DDragon")
            url = f"https://ddragon.leagueoflegends.com/cdn/dragontail-{self.version}.tgz"
            response = requests.get(url)
            extraction_folder = {DDRAGON_FILE} + {self.version}
            os.makedirs(extraction_folder, exist_ok=True)
            with tarfile.open(fileobj=BytesIO(response.content), mode="r:gz") as archive:
                archive.extractall(path=extraction_folder)
            logger.info("Finished downloading and extracting DDragon to {extraction_folder}")
        

    def __read_rune_data(self):
        """
        Reads the rune data from the JSON file in the extracted DDragon folder.

        Returns:
            list: A list of dictionaries containing the rune data.
        """
        logger.info("Reading rune data")
        language = "en_US"

        perk_json_path = f"{DDRAGON_FILE}{self.version}/{self.version}/data/{language}/runesReforged.json"
        with open(perk_json_path, 'r', encoding='utf-8') as file:
            rune_data = json.load(file)
        return rune_data

    def __clean_rune_data(self):
        """
        Cleans the fetched rune data by removing any characters contained between '<' and '>'
        from the long description of the runes.
        """
        logger.info("Cleaning rune data")
        rune_data = []
        self.rune_data = self.__read_rune_data()
        for path in self.rune_data:
            rune_tree = path["name"]
            for runes in path["slots"]:
                for rune in runes["runes"]:
                    cleaned_long_desc = re.sub(r'<[^>]*>', '', rune["longDesc"])
                    rune_data.append([rune["id"], rune_tree, rune["name"], cleaned_long_desc])
        self.rune_data = rune_data

    def __send_rune_data_to_kafka(self, topic):
        """
        Produces the cleaned rune data to a specified Kafka topic.

        Args:
            topic (str): The Kafka topic to send the cleaned rune data to.
        """
        for rune in self.rune_data:
            logger.info(f"Sending rune to {topic}")
            producer.send(topic, rune)

    def produce_rune_data(self, topic):
        """
        Produces the cleaned rune data to a specified Kafka topic.

        Args:
            topic (str): The Kafka topic to send the cleaned rune data to.
        """
        logger.info("Producing rune data")
        self.__download_and_extract_ddragon()
        self.__clean_rune_data()
        self.__send_rune_data_to_kafka(topic)

        # Flush the Kafka producer to ensure all messages are sent
        producer.flush()
    

