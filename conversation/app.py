import yaml
import logging
import logging.config
from gpt_service import GPT_Service
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from truncating_log_handler import TruncatingLogHandler
import urllib.parse

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

@app.get("/gpt_response")
def gpt_response(query: str):
    logger.info(f'Query: {query}')
    gpt_query = urllib.parse.urlencode({'query': query})
    GPT = GPT_Service(gpt_query)
    return GPT.reply

if __name__ == "__main__":    
    # Start the FastAPI application
    uvicorn.run("app:app", host="0.0.0.0", port=8200, reload=True)
# send query to gpt_service then do the logic in there

