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


def prepare_embeddings(embeddings, structure_id_func):
    logger.debug(f'Preparing embeddings')
    return [structure_id_func(embedding, id) for embedding, id in embeddings]


def upload_embeddings(embeddings, service):
    index.upsert(vectors=embeddings, namespace=service)


data_prep = PrepareData()


def structure_matchup(embedding, id):
    date_string = datetime.datetime.now().strftime('%B %d')
    return (f"matchup_{date_string}_{id}", embedding)

def structure_guide(embedding, id):
    return (f"guide_{id}", embedding)

def structure_winrate(embedding, id):
    return (f"winrate_{id}", embedding)

def structure_rune_description(embedding, id):
    logger.debug(f'Embedding rune description: {id}')
    return (f"rune_description_{id}", embedding)
    
def structure_top_rune(embedding, id):
    return (f"top_rune_{id}", embedding)



# def store_dataset_in_pinecone(dataset):
#     exec(f"{dataset} = data_prep.prepare_{dataset}()")
#     exec(f"{dataset}_embeddings = embed_data({dataset})")
#     exec(f"{dataset}_embeddings = prepare_embeddings({dataset}_embeddings, structure_{dataset})")
#     exec(f"upload_embeddings({dataset}_embeddings)")

# store_dataset_in_pinecone('winrates')
# store_dataset_in_pinecone('top_runes')

# matchups = data_prep.prepare_matchups()
# guides = data_prep.prepare_guides()

# winrates = data_prep.prepare_winrates()
# logger.debug(f'embedding winrate data')
# winrate_embeddings = embed_data(winrates)
# logger.debug(f'preparing winrate embeddings')
# winrate_embeddings = prepare_embeddings(winrate_embeddings, structure_winrate)
# logger.debug(f'uploading winrate embeddings')
# upload_embeddings(winrate_embeddings, 'winrates')

# rune_descriptions = data_prep.prepare_rune_descriptions()
# logger.debug(f'embedding rune description data')
# rune_description_embeddings = embed_data(rune_descriptions)
# logger.debug(f'preparing rune description embeddings')
# rune_description_embeddings = prepare_embeddings(rune_description_embeddings, structure_rune_description)
# logger.debug(f'uploading rune description embeddings')
# upload_embeddings(rune_description_embeddings, 'rune_descriptions')

# top_runes = data_prep.prepare_top_runes()
# logger.debug(f'embedding top rune data')
# top_rune_embeddings = embed_data(top_runes)
# logger.debug(f'preparing top rune embeddings')
# top_rune_embeddings = prepare_embeddings(top_rune_embeddings, structure_top_rune)
# logger.debug(f'uploading top rune embeddings')
# upload_embeddings(top_rune_embeddings, 'top_runes')

# logger.debug(f'requesting rune description data')
# rune_descriptions = data_prep.prepare_rune_descriptions()
# # logger.debug(f'embedding rune description data')
# rune_description_embeddings = embed_data(rune_descriptions)
# # logger.debug(f'preparing rune description embeddings')
# # logger.debug(f'length of rune description embeddings: {len(rune_description_embeddings)}')
# rune_description_embeddings = prepare_embeddings(rune_description_embeddings, structure_rune_description)
# # logger.debug(f'uploading rune description embeddings')
# upload_embeddings(rune_description_embeddings)
# logger.debug(f"pinecone rune entries: {index.fetch(ids=['rune_description_0', 'rune_description_1'])}")

def embed_query(query):
    embed_model = "text-embedding-ada-002"

    res = openai.Embedding.create(
        input=query, engine=embed_model
    )
    return res["data"][0]["embedding"]

def query_namespace(query_embedding, namespace, top_k):
    reply = index.query(queries=[query_embedding], top_k=top_k, include_metadata=True, namespace=namespace)
    return reply['results'][0]['matches']

query = "what champion has the highest winrate"
logger.info(f"query: {query}")
query_embedding = embed_query(query)
#logger.info(f"query embedding: {query_embedding}")



winrate_reply = query_namespace(query_embedding, 'winrates', 1)
logger.info(f"pinecone winrate reply: {winrate_reply}")
rune_description_reply = query_namespace(query_embedding, 'rune_descriptions', 1)
logger.info(f"pinecone rune description reply: {rune_description_reply}")
top_rune_reply = query_namespace(query_embedding, 'top_runes', 1)
logger.info(f"pinecone top rune reply: {top_rune_reply}")

services = [(winrate_reply, 'winrates'), (rune_description_reply, 'rune_descriptions'), (top_rune_reply, 'top_runes')]
top_score = {"score": -1, "namespace": '', "id": -1} 

for replies, namespace in services:
    for reply in replies:
        if reply['score'] > top_score["score"]:
            top_score = {"score": reply['score'], "namespace": namespace, "id": reply['id']}

logger.info(f"top reply: {top_score}")
id = re.findall(r'\d+$', top_score['id'])[0]
request_url = f"http://localhost:8000/{top_score['namespace']}/{id}"
logger.info(f"request url: {request_url}")
response = requests.get(request_url)
logger.info(f"response: {response.json()}")


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
