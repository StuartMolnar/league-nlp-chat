import yaml
import logging
import logging.config
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from embed_data import StoreData
from search_vector import SearchVector
from truncating_log_handler import TruncatingLogHandler
from urllib.parse import unquote

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())



def handle_internal_server_error(request, exc):
    """
    Handle internal server errors and log the exception.

    This function logs the exception and returns an appropriate JSON response
    with a 500 Internal Server Error status code.

    Args:
        request (Request): The request that caused the exception.
        exc (Exception): The exception that was raised.

    Returns:
        Response: A response with a 500 Internal Server Error status code,
                  and a content containing the error message and exception details.
    """
    logger.exception(exc)
    return Response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "detail": str(exc)},
        media_type="application/json",
    )

app = FastAPI(exception_handlers={500: handle_internal_server_error})

# Allow CORS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search/")
def search(query: str):
    """
    Accepts a query string, creates a SearchVector object with that query, 
    and then returns the reply from the SearchVector.

    Args:
        query (str): The search query string.

    Returns:
        JSON: The reply from the SearchVector object.
    """
    try:
        query = unquote(query)
        search_vector = SearchVector(query)
        return search_vector.reply
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))



store = StoreData()

@app.post("/store_matchups")
def store_matchups():
    """
    Start the process of updating the matchup data in the vector database.

    This endpoint doesn't require any input. When called, it triggers an update 
    process on the server, which collects and processes the necessary data, 
    and then stores it in the vector database.

    Returns:
        A JSON message indicating the process has been started.
    """
    try:
        store.store_matchups()
        logger.info("Matchup data stored successfully")
        return {"message": "Matchup data stored successfully"}
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/store_guides")
def store_guides():
    """
    Start the process of updating the guide data in the vector database.

    Similar to the matchup endpoint, this doesn't require any input. When called,
    it triggers an update process on the server, which collects and processes the 
    necessary data, and then stores it in the vector database.

    Returns:
        A JSON message indicating the process has been started.
    """
    try:
        store.store_guides()
        logger.info("Guide data stored successfully")
        return {"message": "Guide data stored successfully"}
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/store_winrates")
def store_winrates():
    """
    Start the process of updating the winrate data in the vector database.

    Similar to the matchup endpoint, this doesn't require any input. When called,
    it triggers an update process on the server, which collects and processes the 
    necessary data, and then stores it in the vector database.

    Returns:
        A JSON message indicating the process has been started.
    """
    try:
        store.store_winrates()
        logger.info("Winrate data stored successfully")
        return {"message": "Winrate data stored successfully"}
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/store_rune_descriptions")
def store_rune_descriptions():
    """
    Start the process of updating the rune description data in the vector database.

    Similar to the matchup endpoint, this doesn't require any input. When called,
    it triggers an update process on the server, which collects and processes the 
    necessary data, and then stores it in the vector database.

    Returns:
        A JSON message indicating the process has been started.
    """
    try:
        store.store_rune_descriptions()
        logger.info("Rune description data stored successfully")
        return {"message": "Rune description data stored successfully"}
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/store_top_runes")
def store_top_runes():
    """
    Start the process of updating the top rune data in the vector database.

    Similar to the matchup endpoint, this doesn't require any input. When called,
    it triggers an update process on the server, which collects and processes the 
    necessary data, and then stores it in the vector database.

    Returns:
        A JSON message indicating the process has been started.
    """
    try:
        store.store_top_runes()
        logger.info("Top rune data stored successfully")
        return {"message": "Top rune data stored successfully"}
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":    
    # Start the FastAPI application
    uvicorn.run("app:app", host="0.0.0.0", port=8100, reload=True)