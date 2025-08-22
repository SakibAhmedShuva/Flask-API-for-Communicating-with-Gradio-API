# Flask API for Vietnamese Legal QA
# Integrates with any Gradio API via environment variables

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import logging
import time
from typing import Optional, Dict, Any
from gradio_client import Client
from dotenv import load_dotenv
import threading
from functools import wraps
from datetime import datetime
import traceback

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding to handle unicode characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')

# Enhanced CORS configuration
CORS(app, 
     origins=['*'],  # Allow all origins, configure specifically for production
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'X-API-Key'],
     supports_credentials=True
)

class GradioAPIClient:
    """
    A client class for interacting with any Gradio API
    """
    
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.client = None
        self.last_connected = None
        self.connection_lock = threading.Lock()
        self._connect()
    
    def _connect(self):
        """Establish connection to the API"""
        with self.connection_lock:
            try:
                self.client = Client(self.api_url)
                self.last_connected = datetime.now()
                logger.info(f"Successfully connected to API: {self.api_url}")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to API: {e}")
                self.client = None
                return False
    
    def _ensure_connection(self):
        """Ensure we have a valid connection"""
        if self.client is None:
            if not self._connect():
                raise ConnectionError("Unable to connect to Gradio API")
    
    def generate_response(self, 
                         user_input: str,
                         max_length: float = 512,
                         temperature: float = 0.7,
                         top_p: float = 0.9,
                         endpoint: str = "/generate_response") -> str:
        """
        Generate response using specified endpoint
        """
        self._ensure_connection()
        
        try:
            logger.info(f"Generating response for input: {user_input[:50]}...")
            
            result = self.client.predict(
                user_input=user_input,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                api_name=endpoint
            )
            
            logger.info("Response generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Try to reconnect once
            if self._connect():
                try:
                    result = self.client.predict(
                        user_input=user_input,
                        max_length=max_length,
                        temperature=temperature,
                        top_p=top_p,
                        api_name=endpoint
                    )
                    return result
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
                    raise retry_error
            raise e
    
    def get_lambda_data(self) -> tuple:
        """Get data from the lambda endpoint"""
        self._ensure_connection()
        
        try:
            logger.info("Fetching lambda data...")
            result = self.client.predict(api_name="/lambda")
            logger.info("Lambda data fetched successfully")
            return result
        except Exception as e:
            logger.error(f"Error fetching lambda data: {e}")
            raise

# Initialize the client
API_URL = os.getenv('GRADIO_API_URL', 'https://302463c1bd59d619a7.gradio.live/')
DEFAULT_MAX_LENGTH = float(os.getenv('DEFAULT_MAX_LENGTH', '512'))
DEFAULT_TEMPERATURE = float(os.getenv('DEFAULT_TEMPERATURE', '0.7'))
DEFAULT_TOP_P = float(os.getenv('DEFAULT_TOP_P', '0.9'))
API_KEY = os.getenv('API_KEY')  # Optional API key for authentication

logger.info(f"Initializing with API URL: {API_URL}")

try:
    gradio_client = GradioAPIClient(API_URL)
    logger.info("Gradio client initialized successfully!")
except Exception as e:
    logger.error(f"Failed to initialize Gradio client: {e}")
    gradio_client = None

# Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if API_KEY:
            provided_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            if not provided_key or provided_key != API_KEY:
                return jsonify({
                    'error': 'Invalid or missing API key',
                    'status': 'unauthorized'
                }), 401
        return f(*args, **kwargs)
    return decorated_function

# Error handler decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return jsonify({
                'error': 'Unable to connect to the AI service',
                'status': 'connection_error',
                'message': str(e)
            }), 503
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Internal server error',
                'status': 'error',
                'message': str(e)
            }), 500
    return decorated_function

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if gradio_client and gradio_client.client:
            # Try a simple connection test
            try:
                # Test if we can still connect
                test_client = Client(gradio_client.api_url)
                status = 'healthy'
                code = 200
                message = 'API connection successful'
            except Exception as e:
                logger.warning(f"Health check failed: {e}")
                status = 'unhealthy'
                code = 503
                message = f'API connection failed: {str(e)}'
        else:
            status = 'unhealthy'
            code = 503
            message = 'Gradio client not initialized'
    except Exception as e:
        logger.error(f"Health check error: {e}")
        status = 'error'
        code = 500
        message = f'Health check error: {str(e)}'
    
    return jsonify({
        'status': status,
        'message': message,
        'api_url': API_URL,
        'last_connected': gradio_client.last_connected.isoformat() if gradio_client and gradio_client.last_connected else None,
        'timestamp': datetime.now().isoformat()
    }), code

# Main generation endpoint
@app.route('/generate', methods=['POST'])
@require_api_key
@handle_errors
def generate_response():
    """Generate response from Vietnamese Legal QA model"""
    if not gradio_client:
        return jsonify({
            'error': 'Gradio client not initialized',
            'status': 'service_unavailable'
        }), 503
    
    data = request.get_json()
    if not data:
        return jsonify({
            'error': 'No JSON data provided',
            'status': 'bad_request'
        }), 400
    
    # Validate required parameters
    user_input = data.get('user_input') or data.get('question')
    if not user_input:
        return jsonify({
            'error': 'user_input or question is required',
            'status': 'bad_request'
        }), 400
    
    # Extract parameters with defaults
    max_length = data.get('max_length', DEFAULT_MAX_LENGTH)
    temperature = data.get('temperature', DEFAULT_TEMPERATURE)
    top_p = data.get('top_p', DEFAULT_TOP_P)
    endpoint = data.get('endpoint', '/generate_response')
    
    # Validate parameters
    if not (1 <= max_length <= 2048):
        max_length = DEFAULT_MAX_LENGTH
    if not (0.0 <= temperature <= 2.0):
        temperature = DEFAULT_TEMPERATURE
    if not (0.0 <= top_p <= 1.0):
        top_p = DEFAULT_TOP_P
    
    # Generate response
    response = gradio_client.generate_response(
        user_input=user_input,
        max_length=max_length,
        temperature=temperature,
        top_p=top_p,
        endpoint=endpoint
    )
    
    return jsonify({
        'status': 'success',
        'user_input': user_input,
        'response': response,
        'parameters': {
            'max_length': max_length,
            'temperature': temperature,
            'top_p': top_p,
            'endpoint': endpoint
        },
        'timestamp': datetime.now().isoformat()
    })

# Alternative endpoint for GET requests
@app.route('/ask', methods=['GET'])
@require_api_key
@handle_errors
def ask_question():
    """Ask a question via GET request"""
    if not gradio_client:
        return jsonify({
            'error': 'Gradio client not initialized',
            'status': 'service_unavailable'
        }), 503
    
    question = request.args.get('question') or request.args.get('q')
    if not question:
        return jsonify({
            'error': 'question parameter is required',
            'status': 'bad_request'
        }), 400
    
    # Extract parameters with defaults
    max_length = float(request.args.get('max_length', DEFAULT_MAX_LENGTH))
    temperature = float(request.args.get('temperature', DEFAULT_TEMPERATURE))
    top_p = float(request.args.get('top_p', DEFAULT_TOP_P))
    
    response = gradio_client.generate_response(
        user_input=question,
        max_length=max_length,
        temperature=temperature,
        top_p=top_p
    )
    
    return jsonify({
        'status': 'success',
        'question': question,
        'response': response,
        'timestamp': datetime.now().isoformat()
    })

# Compare endpoints
@app.route('/compare', methods=['POST'])
@require_api_key
@handle_errors
def compare_endpoints():
    """Compare responses from both generation endpoints"""
    if not gradio_client:
        return jsonify({
            'error': 'Gradio client not initialized',
            'status': 'service_unavailable'
        }), 503
    
    data = request.get_json()
    if not data:
        return jsonify({
            'error': 'No JSON data provided',
            'status': 'bad_request'
        }), 400
    
    user_input = data.get('user_input') or data.get('question')
    if not user_input:
        return jsonify({
            'error': 'user_input or question is required',
            'status': 'bad_request'
        }), 400
    
    max_length = data.get('max_length', DEFAULT_MAX_LENGTH)
    temperature = data.get('temperature', DEFAULT_TEMPERATURE)
    top_p = data.get('top_p', DEFAULT_TOP_P)
    
    # Generate responses from both endpoints
    response1 = gradio_client.generate_response(
        user_input=user_input,
        max_length=max_length,
        temperature=temperature,
        top_p=top_p,
        endpoint="/generate_response"
    )
    
    time.sleep(0.5)  # Small delay between requests
    
    response2 = gradio_client.generate_response(
        user_input=user_input,
        max_length=max_length,
        temperature=temperature,
        top_p=top_p,
        endpoint="/generate_response_1"
    )
    
    return jsonify({
        'status': 'success',
        'user_input': user_input,
        'responses': {
            'endpoint_1': response1,
            'endpoint_2': response2
        },
        'parameters': {
            'max_length': max_length,
            'temperature': temperature,
            'top_p': top_p
        },
        'timestamp': datetime.now().isoformat()
    })

# Lambda endpoint
@app.route('/sample', methods=['GET'])
@require_api_key
@handle_errors
def get_sample_data():
    """Get sample data from lambda endpoint"""
    if not gradio_client:
        return jsonify({
            'error': 'Gradio client not initialized',
            'status': 'service_unavailable'
        }), 503
    
    question, response = gradio_client.get_lambda_data()
    
    return jsonify({
        'status': 'success',
        'sample_question': question,
        'sample_response': response,
        'timestamp': datetime.now().isoformat()
    })

# Batch processing endpoint
@app.route('/batch', methods=['POST'])
@require_api_key
@handle_errors
def batch_generate():
    """Process multiple questions in batch"""
    if not gradio_client:
        return jsonify({
            'error': 'Gradio client not initialized',
            'status': 'service_unavailable'
        }), 503
    
    data = request.get_json()
    if not data:
        return jsonify({
            'error': 'No JSON data provided',
            'status': 'bad_request'
        }), 400
    
    questions = data.get('questions', [])
    if not questions or not isinstance(questions, list):
        return jsonify({
            'error': 'questions array is required',
            'status': 'bad_request'
        }), 400
    
    if len(questions) > 10:  # Limit batch size
        return jsonify({
            'error': 'Maximum 10 questions allowed per batch',
            'status': 'bad_request'
        }), 400
    
    max_length = data.get('max_length', DEFAULT_MAX_LENGTH)
    temperature = data.get('temperature', DEFAULT_TEMPERATURE)
    top_p = data.get('top_p', DEFAULT_TOP_P)
    delay = data.get('delay', 1.0)  # Delay between requests
    
    results = []
    for i, question in enumerate(questions):
        try:
            response = gradio_client.generate_response(
                user_input=question,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p
            )
            
            results.append({
                'index': i,
                'question': question,
                'response': response,
                'status': 'success'
            })
            
            # Rate limiting
            if i < len(questions) - 1:
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"Error processing question {i+1}: {e}")
            results.append({
                'index': i,
                'question': question,
                'response': None,
                'error': str(e),
                'status': 'error'
            })
    
    return jsonify({
        'status': 'completed',
        'total_questions': len(questions),
        'results': results,
        'parameters': {
            'max_length': max_length,
            'temperature': temperature,
            'top_p': top_p,
            'delay': delay
        },
        'timestamp': datetime.now().isoformat()
    })

# Web interface (root route)
@app.route('/', methods=['GET'])
def index():
    """Main web interface"""
    return render_template('index.html', 
                         api_url=API_URL,
                         has_api_key=bool(API_KEY))

# API documentation endpoint
@app.route('/docs', methods=['GET'])
@app.route('/api-docs', methods=['GET'])
def api_documentation():
    """API documentation"""
    docs = {
        'name': 'Vietnamese Legal QA API',
        'version': '1.0.0',
        'description': 'Flask API wrapper for Vietnamese Legal QA Gradio service',
        'base_url': request.base_url.rstrip('/'),
        'gradio_api_url': API_URL,
        'authentication': 'API Key required (if configured)' if API_KEY else 'No authentication required',
        'endpoints': {
            'GET /': 'Web interface',
            'GET /docs': 'This documentation',
            'GET /health': 'Health check',
            'POST /generate': 'Generate response (main endpoint)',
            'GET /ask': 'Ask question via GET request',
            'POST /compare': 'Compare responses from both endpoints',
            'GET /sample': 'Get sample data from lambda endpoint',
            'POST /batch': 'Process multiple questions in batch'
        },
        'example_requests': {
            'generate': {
                'url': '/generate',
                'method': 'POST',
                'body': {
                    'user_input': 'What are the labor laws in Vietnam?',
                    'max_length': 512,
                    'temperature': 0.7,
                    'top_p': 0.9
                }
            },
            'ask': {
                'url': '/ask?question=What are the basic rights?',
                'method': 'GET'
            },
            'batch': {
                'url': '/batch',
                'method': 'POST',
                'body': {
                    'questions': ['Question 1', 'Question 2'],
                    'delay': 1.0
                }
            }
        },
        'environment_variables': {
            'GRADIO_API_URL': 'Gradio API URL (required)',
            'API_KEY': 'API key for authentication (optional)',
            'DEFAULT_MAX_LENGTH': 'Default max response length (default: 512)',
            'DEFAULT_TEMPERATURE': 'Default temperature (default: 0.7)',
            'DEFAULT_TOP_P': 'Default top_p (default: 0.9)'
        }
    }
    
    return jsonify(docs)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))  # Default to 5000 instead of 7860
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting Flask API on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Using Gradio API: {API_URL}")
    
    app.run(host=host, port=port, debug=debug)