import yaml
import logging
import logging.config
from gpt_service import GPT_Service
from fastapi import FastAPI, HTTPException, Response, status, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic.error_wrappers import ValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from truncating_log_handler import TruncatingLogHandler
import urllib.parse
from typing import Any, Dict
from pydantic import BaseModel

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

class GPTResponse(BaseModel):
    reply: str   

def handle_internal_server_error(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle internal server errors and log the exception.

    This function logs the exception and returns an appropriate JSON response
    with a 500 Internal Server Error status code.

    Args:
        request (Request): The incoming request that triggered the exception.
        exc (Exception): The exception that was raised.

    Returns:
        JSONResponse: A JSON response with a 500 Internal Server Error status code,
                      and a content containing the error message and exception details.
    """
    logger.exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "detail": str(exc)},
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

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle Request Validation errors caused by incorrect data in the request body.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle all HTTPExceptions, used when raising exceptions within your route handlers.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.get("/gpt_response", response_model=GPTResponse)
def gpt_response(query: str) -> Dict[str, Any]:
    """
    Returns GPT-3.5 generated reply to the provided query.
    
    Args:
        query (str): The query for which to generate a response.
        
    Returns:
        dict: A dictionary containing the GPT-3.5 generated reply.
    """
    logger.info(f'Received request for GPT-3.5 response to query: {query}')
    
    try:
        gpt_query = urllib.parse.urlencode({'query': query})
        GPT = GPT_Service(gpt_query)
        response = {"reply": GPT.reply}
        logger.info(f'Successfully generated GPT-3.5 response for query: {query}')
        return response
    except Exception as e:
        logger.error(f'Error generating GPT-3.5 response for query: {query} - {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":    
    # Start the FastAPI application
    uvicorn.run("app:app", host="0.0.0.0", port=8200, reload=True)

