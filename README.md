# Flask API for Vietnamese Legal QA

A Flask-based REST API wrapper that provides seamless integration with Vietnamese Legal QA Gradio services. This project offers a professional web interface and RESTful endpoints for interacting with AI-powered Vietnamese legal question-answering systems.

## Features

- **RESTful API Endpoints**: Clean HTTP endpoints for AI model interaction
- **Web Interface**: Professional responsive web UI built with Tailwind CSS
- **Real-time Health Monitoring**: Automatic API health checks and status reporting
- **Flexible Configuration**: Environment-based configuration with sensible defaults
- **Authentication Support**: Optional API key authentication
- **Batch Processing**: Handle multiple questions efficiently
- **Endpoint Comparison**: Compare responses from different AI endpoints
- **Error Handling**: Comprehensive error handling and logging
- **CORS Support**: Cross-origin resource sharing for web applications

## Quick Start

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SakibAhmedShuva/Flask-API-for-Communicating-with-Gradio-API.git
   cd Flask-API-for-Communicating-with-Gradio-API
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:7860`

## Configuration

Create a `.env` file in the project root:

```env
# Gradio API URL (Required)
GRADIO_API_URL=https://your-gradio-api-url.com/

# API Authentication (Optional)
API_KEY=your-secret-api-key-here

# Default Parameters
DEFAULT_MAX_LENGTH=512
DEFAULT_TEMPERATURE=0.7
DEFAULT_TOP_P=0.9

# Flask Configuration
PORT=7860
HOST=0.0.0.0
FLASK_DEBUG=False
```

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web interface |
| `GET` | `/health` | API health check |
| `GET` | `/docs` | API documentation |

### Question & Answer

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate` | Generate AI response (main endpoint) |
| `GET` | `/ask` | Ask question via GET request |
| `POST` | `/compare` | Compare responses from multiple endpoints |
| `GET` | `/sample` | Get sample question-answer pair |
| `POST` | `/batch` | Process multiple questions |

## Usage Examples

### Generate Response

```bash
curl -X POST http://localhost:7860/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "What are the labor laws in Vietnam?",
    "max_length": 512,
    "temperature": 0.7,
    "top_p": 0.9
  }'
```

### Ask Question (GET)

```bash
curl "http://localhost:7860/ask?question=What are Vietnamese tax obligations?"
```

### Batch Processing

```bash
curl -X POST http://localhost:7860/batch \
  -H "Content-Type: application/json" \
  -d '{
    "questions": [
      "What are employee rights in Vietnam?",
      "How to register a company in Vietnam?"
    ],
    "delay": 1.0
  }'
```

### Health Check

```bash
curl http://localhost:7860/health
```

## Request/Response Format

### POST /generate

**Request:**
```json
{
  "user_input": "Your legal question here",
  "max_length": 512,
  "temperature": 0.7,
  "top_p": 0.9
}
```

**Response:**
```json
{
  "status": "success",
  "user_input": "Your legal question here",
  "response": "AI-generated response...",
  "parameters": {
    "max_length": 512,
    "temperature": 0.7,
    "top_p": 0.9
  },
  "timestamp": "2025-08-22T12:00:00"
}
```

### Error Response

```json
{
  "error": "Error description",
  "status": "error_type",
  "message": "Detailed error message"
}
```

## Authentication

If an API key is configured via the `API_KEY` environment variable, include it in requests:

**Header:**
```
X-API-Key: your-api-key-here
```

**Query parameter:**
```
?api_key=your-api-key-here
```

## Parameters

### AI Generation Parameters

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `max_length` | float | 1-2048 | 512 | Maximum response length |
| `temperature` | float | 0.0-2.0 | 0.7 | Response creativity (higher = more creative) |
| `top_p` | float | 0.0-1.0 | 0.9 | Response focus (lower = more focused) |

## Web Interface

Access the interactive web interface at `http://localhost:7860` which includes:

- **Chat Interface**: Ask questions and view AI responses
- **Parameter Controls**: Adjust AI generation settings in real-time
- **Sample Questions**: Quick-start with predefined legal questions
- **Health Status**: Real-time API connection status
- **Comparison Tool**: Compare responses from different endpoints

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │────│   Flask API     │────│   Gradio API    │
│                 │    │                 │    │                 │
│ - Web Interface │    │ - REST Endpoints│    │ - AI Model      │
│ - Direct HTTP   │    │ - Authentication│    │ - Generation    │
│ - JavaScript    │    │ - Error Handling│    │ - Processing    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Development

### Project Structure

```
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── .env               # Environment configuration
├── .gitignore         # Git ignore file
├── LICENSE            # MIT license
├── api.log            # Application logs
├── templates/         # HTML templates
│   └── index.html     # Web interface
└── static/           # Static assets (CSS, JS)
```

### Adding New Endpoints

1. Define the endpoint function in `app.py`
2. Use the `@handle_errors` decorator for error handling
3. Use `@require_api_key` decorator if authentication is needed
4. Update the API documentation in the `/docs` endpoint

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GRADIO_API_URL` | Yes | None | URL of the Gradio API service |
| `API_KEY` | No | None | API key for authentication |
| `DEFAULT_MAX_LENGTH` | No | 512 | Default maximum response length |
| `DEFAULT_TEMPERATURE` | No | 0.7 | Default generation temperature |
| `DEFAULT_TOP_P` | No | 0.9 | Default top-p value |
| `PORT` | No | 7860 | Flask server port |
| `HOST` | No | 0.0.0.0 | Flask server host |
| `FLASK_DEBUG` | No | False | Enable Flask debug mode |

## Dependencies

- **Flask 3.1.2**: Web framework
- **flask-cors 5.0.1**: Cross-origin resource sharing
- **gradio-client 1.12.1**: Gradio API client
- **python-dotenv 1.1.1**: Environment variable management

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "app.py"]
```

### Production Considerations

- Use a production WSGI server (e.g., Gunicorn, uWSGI)
- Set up proper logging configuration
- Configure environment-specific CORS settings
- Implement rate limiting for production use
- Set up monitoring and alerting
- Use HTTPS in production

## Monitoring & Logging

The application includes comprehensive logging:

- **File Logging**: All events logged to `api.log`
- **Console Logging**: Real-time log output
- **UTF-8 Support**: Proper Unicode character handling
- **Health Checks**: Automatic API connectivity monitoring
- **Error Tracking**: Detailed error logging with stack traces

## Error Handling

The API implements robust error handling:

- **Connection Errors**: Automatic retry logic for API connections
- **Validation Errors**: Input parameter validation
- **Authentication Errors**: API key validation
- **Service Errors**: Graceful handling of upstream service issues
- **Rate Limiting**: Built-in protection against excessive requests

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/new-feature`)
7. Create a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: API documentation available at `/docs` endpoint
- **Health Status**: Monitor API health via `/health` endpoint

## Changelog

### v1.0.0
- Initial release
- Flask API wrapper for Gradio services
- Web interface with real-time chat
- Batch processing capabilities
- Health monitoring and error handling
- Optional authentication support

---

**Author**: Sakib Ahmed  
**Repository**: [Flask-API-for-Communicating-with-Gradio-API](https://github.com/SakibAhmedShuva/Flask-API-for-Communicating-with-Gradio-API)
