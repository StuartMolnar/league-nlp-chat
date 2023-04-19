import connexion
from connexion import NoContent, request
import yaml
import logging
import logging.config
from gpt_service import generate_response

def ask():
    request_body = request.json
    user_input = request_body["user_input"]
    response = generate_response(user_input)
    return {"response": response}


app = connexion.FlaskApp(__name__, specification_dir='')
#CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yaml",
            strict_validation=True,
            validate_responses=True)

if __name__ == "__main__":
    app.run(port=8100, use_reloader=False)
