from http import HTTPStatus
from flask import redirect
import logging.config
from config import LOGGING_CONFIG
from flask_openapi3 import OpenAPI, Info, Tag
from flask_cors import CORS
from routes import BLUEPRINTS


info = Info(title="StackUp", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
logger.info("Api inicializada com sucesso")

# Registrar blueprints
for blueprint in BLUEPRINTS:
    app.register_api(blueprint)

# tags
home_tag = Tag(name="Documentação", description="Documentação: Swagger")


@app.route('/')
def index():
    return redirect('/openapi')
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
