import requests
import json
import tarfile
import os
import shutil
from io import BytesIO

import logging
import logging.config
import yaml
from kafka import KafkaProducer

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

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())


class DDragonRunes:
    def __init__(self):
        self.latest_version = self.__get_latest_version()
        self.language = "en_US"

    def __get_latest_version(self):
        ddragon_versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
        response = requests.get(ddragon_versions_url)
        versions = json.loads(response.text)
        return versions[0]
    
    def __is_newer_version(self):
        previous_version = app_config['ddragon']['current_version']
        new_version = self.__get_latest_version()
        if new_version > previous_version:
            app_config['ddragon']['current_version'] = new_version
            return True
        return False


    def download_and_extract_ddragon(self):
        url = f"https://ddragon.leagueoflegends.com/cdn/dragontail-{self.latest_version}.tgz"
        response = requests.get(url)
        with tarfile.open(fileobj=BytesIO(response.content), mode="r:gz") as archive:
            archive.extractall()

    def read_rune_data(self):
        perk_json_path = f"dragontail-{self.latest_version}/data/{self.language}/perk.json"
        with open(perk_json_path, 'r', encoding='utf-8') as file:
            rune_data = json.load(file)
        return rune_data

    def print_runes(self):
        rune_data = self.read_rune_data()
        for rune in rune_data:
            print(f"Rune name: {rune['name']}")
            print(f"Description: {rune['shortDesc']}")
            print("\n")

    def clean_up(self):
        shutil.rmtree(f"dragontail-{self.latest_version}")

if __name__ == "__main__":
    ddragon = DDragonRunes()
    ddragon.download_and_extract_ddragon()
    ddragon.print_runes()
    ddragon.clean_up()