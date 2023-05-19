import os
import openai
import pinecone
import yaml
import logging
import logging.config
from dotenv import load_dotenv
from prepare_data import PrepareData
import datetime
import requests
import re

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

load_dotenv()
openai.api_key = os.getenv("GPT_KEY")
pinecone.init(api_key=os.getenv("PINECONE_KEY"), environment="asia-northeast1-gcp")

index = pinecone.Index(pinecone.list_indexes()[0])

class EmbedData:
    def __init__(self):
        self.data_prep = PrepareData()

    @staticmethod
    def embed_data(data):
        def embed_item(item):
            embed_model = "text-embedding-ada-002"
            text, id = item
            res = openai.Embedding.create(
                input=text, engine=embed_model
            )
            return res["data"][0]["embedding"], id
        embeddings = [embed_item(item) for item in data]
        return embeddings

    @staticmethod
    def __prepare_embeddings(embeddings, structure_id_func):
        logger.info(f'Preparing embeddings')
        return [structure_id_func(embedding, id) for embedding, id in embeddings]
    
    @staticmethod
    def __upload_embeddings(embeddings, service, batch_size=100):
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

    def store_matchups(self):
        logger.info(f"preparing matchup data")
        matchups = self.data_prep.prepare_matchups()
        logger.info(f'embedding matchup data')
        matchup_embeddings = self.embed_data(matchups)
        logger.info(f'preparing matchup embeddings')
        matchup_embeddings = self.__prepare_embeddings(matchup_embeddings, self.__structure_matchup)
        logger.info(f'uploading matchup embeddings')
        self.__upload_embeddings(matchup_embeddings, 'matchups')
        logger.info("matchup entries uploaded")

    def store_guides(self):
        logger.info(f"preparing guide data")
        guides = self.data_prep.prepare_guides()
        logger.info(f'embedding guide data')
        guide_embeddings = self.embed_data(guides)
        logger.info(f'preparing guide embeddings')
        guide_embeddings = self.__prepare_embeddings(guide_embeddings, self.__structure_guide)
        logger.info(f'uploading guide embeddings')
        self.__upload_embeddings(guide_embeddings, 'guides')
        logger.info("guide entries uploaded")

    def store_winrates(self):
        logger.info(f"preparing winrate data")
        winrates = self.data_prep.prepare_winrates()
        logger.info(f'embedding winrate data')
        winrate_embeddings = self.embed_data(winrates)
        logger.info(f'preparing winrate embeddings')
        winrate_embeddings = self.__prepare_embeddings(winrate_embeddings, self.__structure_winrate)
        logger.info(f'uploading winrate embeddings')
        self.__upload_embeddings(winrate_embeddings, 'winrates')
        logger.info("winrate entries uploaded")

    def store_rune_descriptions(self):
        logger.info(f"preparing rune description data")
        rune_descriptions = self.data_prep.prepare_rune_descriptions()
        logger.info(f'embedding rune description data')
        rune_description_embeddings = self.embed_data(rune_descriptions)
        logger.info(f'preparing rune description embeddings')
        rune_description_embeddings = self.__prepare_embeddings(rune_description_embeddings, self.__structure_rune_description)
        logger.info(f'uploading rune description embeddings')
        self.__upload_embeddings(rune_description_embeddings, 'rune_descriptions')
        logger.info("rune entries uploaded")

    def store_top_runes(self):
        logger.info(f"preparing top rune data")
        top_runes = self.data_prep.prepare_top_runes()
        logger.info(f'embedding top rune data')
        top_rune_embeddings = self.embed_data(top_runes)
        logger.info(f'preparing top rune embeddings')
        top_rune_embeddings = self.__prepare_embeddings(top_rune_embeddings, self.__structure_top_rune)
        logger.info(f'uploading top rune embeddings')
        self.__upload_embeddings(top_rune_embeddings, 'top_runes')
        logger.info("top rune entries uploaded")

# EmbedData = EmbedData()
# EmbedData.store_matchups()


# def embed_query(query):
#     embed_model = "text-embedding-ada-002"

#     res = openai.Embedding.create(
#         input=query, engine=embed_model
#     )
#     return res["data"][0]["embedding"]

# def query_namespace(query_embedding, namespace, top_k):
#     reply = index.query(queries=[query_embedding], top_k=top_k, include_metadata=True, namespace=namespace)
#     return reply['results'][0]['matches']

# query = "how do i play rakan early game"
# logger.info(f"query: {query}")
# query_embedding = embed_query(query)
# #logger.info(f"query embedding: {query_embedding}")

# matchup_reply = query_namespace(query_embedding, 'matchups', 3)
# logger.info(f"pinecone matchup reply: {matchup_reply}")
# guide_reply = query_namespace(query_embedding, 'guides', 1)
# logger.info(f"pinecone guide reply: {guide_reply}")
# winrate_reply = query_namespace(query_embedding, 'winrates', 1)
# logger.info(f"pinecone winrate reply: {winrate_reply}")
# rune_description_reply = query_namespace(query_embedding, 'rune_descriptions', 1)
# logger.info(f"pinecone rune description reply: {rune_description_reply}")
# top_rune_reply = query_namespace(query_embedding, 'top_runes', 1)
# logger.info(f"pinecone top rune reply: {top_rune_reply}")

# services = [(matchup_reply, 'matchups'), (guide_reply, 'guides'), (winrate_reply, 'winrates'), (rune_description_reply, 'rune_descriptions'), (top_rune_reply, 'top_runes')]
# top_score = {"score": -1, "namespace": '', "id": -1} 

# for replies, namespace in services:
#     for reply in replies:
#         if reply['score'] > top_score["score"]:
#             top_score = {"score": reply['score'], "namespace": namespace, "id": reply['id']}

# logger.info(f"top reply: {top_score}")
# id = re.findall(r'\d+$', top_score['id'])[0]
# request_url = f"http://localhost:8000/{top_score['namespace']}/{id}"
# logger.info(f"request url: {request_url}")
# response = requests.get(request_url)
# logger.info(f"response: {response.json()}")


# !!!!!!!!!!!!!!!!!!!!!!

# !!!!!!!!!!!!!!!!!!!!!!















# for match in reply['results'][0]['matches']:
#     logger.info(f"pinecone result: {match['values']}")


# todo: test the vector search by hardcoding a question, then embedding it, then searching for the closest vector






# 410 matchups = $0.0085
# guides = $0.5948
# winrates = $0.0009
# rune descriptions = $0.0017
# top runes = $0.0020
