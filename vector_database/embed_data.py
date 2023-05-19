import os
import openai
import pinecone
import yaml
import logging
import logging.config
from dotenv import load_dotenv
from prepare_data import PrepareData
import datetime

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

load_dotenv()
openai.api_key = os.getenv("GPT_KEY")
pinecone.init(api_key=os.getenv("PINECONE_KEY"), environment="asia-northeast1-gcp")

index = pinecone.Index(pinecone.list_indexes()[0])

class StoreData:
    """
    A class to handle the preparation and uploading of different types of data to a pinecone database.

    Attributes:
        None

    Methods:
        store_matchups()

        store_guides()

        store_winrates()

        store_rune_descriptions()

        store_top_runes()
    """

    def __init__(self):
        """
        Initializes the StoreData instance.
        """
        self.data_prep = PrepareData()

    @staticmethod
    def __embed_data(data):
        """
        Embeds the given data using OpenAI.

        Args:
            data (list): A list of data to be embedded.

        Returns:
            list: A list of tuples where the first element is the embedding vector and the second element is the ID of the data.
        """
        def embed_item(item):
            embed_model = app_config['models']['embed_model']
            text, id = item
            res = openai.Embedding.create(
                input=text, engine=embed_model
            )
            return res["data"][0]["embedding"], id
        embeddings = [embed_item(item) for item in data]
        return embeddings

    @staticmethod
    def __prepare_embeddings(embeddings, structure_id_func):
        """    
        Prepares the embeddings for upload by structuring them and their IDs.

        Args:
            embeddings (list): A list of embeddings.
            structure_id_func (func): A function to structure the IDs for each embedding.

        Returns:
            list: A list of structured embeddings.
        """
        logger.info(f'Preparing embeddings')
        return [structure_id_func(embedding, id) for embedding, id in embeddings]
    
    @staticmethod
    def __upload_embeddings(embeddings, service, batch_size=100):
        """
        Uploads the embeddings to the specified service.

        Args:
            embeddings (list): A list of embeddings to upload.
            service (str): The name of the service to upload to.
            batch_size (int, optional): The number of embeddings to upload at once. Defaults to 100.
        """
        for i in range(0, len(embeddings), batch_size):
            batch = embeddings[i:i+batch_size]
            try:
                index.upsert(vectors=batch, namespace=service)
            except Exception as e:
                logger.error(f"An error occurred while uploading embeddings: {e}")

    
    @staticmethod
    def __structure_matchup(embedding, id):
        date_string = datetime.datetime.now().strftime('%B %d')
        return (f"matchup_{date_string}_{id}", embedding)

    @staticmethod
    def __structure_guide(embedding, id):
        return (f"guide_{id}", embedding)

    @staticmethod
    def __structure_winrate(embedding, id):
        return (f"winrate_{id}", embedding)

    def __structure_rune_description(self, embedding, id):
        logger.info(f'Embedding rune description: {id}')
        return (f"rune_description_{id}", embedding)

    @staticmethod
    def __structure_top_rune(embedding, id):
        return (f"top_rune_{id}", embedding)
    
    def __store_data(self, data_type, prepare_func, structure_func):
        """
        Prepares, embeds, and uploads a specified type of data.

        Args:
            data_type (str): The type of data to handle.
            prepare_func (func): A function to prepare the data for embedding.
            structure_func (func): A function to structure the embeddings for upload.
        """
        logger.info(f"preparing {data_type} data")
        data = getattr(self.data_prep, prepare_func)()
        
        logger.info(f'embedding {data_type} data')
        data_embeddings = self.__embed_data(data)
        
        logger.info(f'preparing {data_type} embeddings')
        data_embeddings = self.__prepare_embeddings(data_embeddings, structure_func)
        
        logger.info(f'uploading {data_type} embeddings')
        self.__upload_embeddings(data_embeddings, data_type)
        
        logger.info(f"{data_type} entries uploaded")

    def store_matchups(self):
        """
        Prepares, embeds, and uploads matchup data.
        """
        self.__store_data('matchups', 'prepare_matchups', self.__structure_matchup)

    def store_guides(self):
        """
        Prepares, embeds, and uploads guide data.
        """
        self.__store_data('guides', 'prepare_guides', self.__structure_guide)

    def store_winrates(self):
        """
        Prepares, embeds, and uploads winrate data.
        """
        self.__store_data('winrates', 'prepare_winrates', self.__structure_winrate)

    def store_rune_descriptions(self):
        """
        Prepares, embeds, and uploads rune description data.
        """
        self.__store_data('rune_descriptions', 'prepare_rune_descriptions', self.__structure_rune_description)

    def store_top_runes(self):
        """
        Prepares, embeds, and uploads top rune data.
        """
        self.__store_data('top_runes', 'prepare_top_runes', self.__structure_top_rune)


