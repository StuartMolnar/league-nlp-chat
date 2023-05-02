import yaml
from sqlalchemy import create_engine
from base import Base
from challenger_matchups import ChallengerMatchup
from champion_guides import ChampionGuide

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    # Replace the placeholder with the actual value from the environment variable
    # config['database']['password'] = os.environ.get('DB_PASSWORD')
    return config

db_config = load_config('app_conf.yml')

DATABASE_URL = f"mysql+pymysql://{db_config['database']['username']}:{db_config['database']['password']}@{db_config['database']['hostname']}:{db_config['database']['port']}/{db_config['database']['name']}"

engine = create_engine(DATABASE_URL)

# Create all defined tables
Base.metadata.create_all(bind=engine, tables=[ChallengerMatchup.__table__, ChampionGuide.__table__])