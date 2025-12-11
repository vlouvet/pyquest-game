"""
API Documentation Endpoint

Serves Swagger UI for API documentation.
"""
from flask import send_from_directory, render_template_string
from flask_swagger_ui import get_swaggerui_blueprint
from . import api_v1
import os


# Swagger UI configuration
SWAGGER_URL = '/api/v1/docs'
API_SPEC_URL = '/api/v1/openapi.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_SPEC_URL,
    config={
        'app_name': "PyQuest API",
        'deepLinking': True,
        'displayRequestDuration': True
    }
)


@api_v1.route('/openapi.yaml')
def get_openapi_spec():
    """Serve the OpenAPI specification file"""
    from flask import current_app, send_file
    spec_path = os.path.join(
        current_app.root_path,
        'api',
        'openapi.yaml'
    )
    return send_file(spec_path, mimetype='text/yaml')


@api_v1.route('/docs')
def api_docs_redirect():
    """Redirect to Swagger UI documentation"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PyQuest API Documentation</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css">
        <style>
            body { margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: "{{ url_for('api_v1.get_openapi_spec') }}",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                });
                window.ui = ui;
            };
        </script>
    </body>
    </html>
    """)


@api_v1.route('/')
def api_root():
    """API root endpoint with basic information"""
    return {
        'name': 'PyQuest API',
        'version': '1.0.0',
        'description': 'RESTful API for PyQuest game',
        'documentation': '/api/v1/docs',
        'endpoints': {
            'authentication': '/api/v1/auth',
            'player': '/api/v1/player',
            'tiles': '/api/v1/player/{player_id}/tiles',
            'combat': '/api/v1/player/{player_id}/combat'
        }
    }
