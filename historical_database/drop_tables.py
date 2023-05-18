from sqlalchemy import create_engine, Table, MetaData
from base import Base
import yaml
import logging
import logging.config
from challenger_matchups import ChallengerMatchup
from champion_guides import ChampionGuide
from top_runes import TopRunes
from rune_descriptions import RuneDescription
from champion_winrates import ChampionWinrates

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    # Replace the placeholder with the actual value from the environment variable
    # config['database']['password'] = os.environ.get('DB_PASSWORD')
    return config

db_config = load_config('app_conf.yml')
DATABASE_URL = f"mysql+pymysql://{db_config['database']['username']}:{db_config['database']['password']}@{db_config['database']['hostname']}:{db_config['database']['port']}/{db_config['database']['name']}"

logger.info("Dropping all tables")

engine = create_engine(DATABASE_URL)

# Drop all tables that have been created using the Base class
Base.metadata.drop_all(bind=engine)
logger.info("Tables dropped successfully")