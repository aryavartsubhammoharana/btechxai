import json
import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from sarvamai import SarvamAI

# ─ INITIALIZATION ─
app = Flask(__name__, template_folder='templates', static_folder='.', static_url_path='')
CORS(app)  # Enables cross-origin requests from frontend


API_KEY = os.environ.get("SARVAM_API_KEY")
client = SarvamAI(api_subscription_key=API_KEY)

# ─ SYSTEM CONFIGURATION ─
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are BTechX AI — an intelligent assistant with deep knowledge of Indian culture, "
        "history, languages, science, and technology. You are a cultural ambassador who shares "
        "insights and stories that enrich the user's understanding of India's rich heritage. "
        "You are also highly knowledgeable about Computer Science, engineering, and academics. "
        "Respond in a natural, warm, and contextually aware manner. "
        "Keep your responses clear and concise. Do not use markdown formatting symbols like #, *, ** in your response."
    )
}

# ─ HELPER FUNCTIONS ─
def get_timestamp():
    """Return current timestamp for logging."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_message(level, message):
    """Log messages with timestamp."""
    prefix = f"[{get_timestamp()}] [{level}]"
    print(f"{prefix} {message}")
    sys.stdout.flush()

def clean_response(text: str) -> str:
    """Remove markdown formatting symbols from AI response."""
    markdown_symbols = ['####', '###', '##', '#', '***', '**', '*', '`', '```']
    for symbol in markdown_symbols:
        text = text.replace(symbol, '')
    return text.strip()

def validate_request(data: dict) -> tuple[bool, str]:
    """Validate incoming request data."""
    if not data:
        return False, "Request body is empty"
    
    message = data.get('message', '').strip()
    if not message:
        return False, "Message field is empty or missing"
    
    if len(message) > 5000:
        return False, "Message exceeds maximum length (5000 characters)"
    
    history = data.get('history', [])
    if not isinstance(history, list):
        return False, "History must be a list"
    
    return True, ""

# ─ API ENDPOINTS ─
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'BTechX AI Server',
        'timestamp': get_timestamp()
    }), 200

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint."""
    try:
        data = request.get_json()
        
        # Validate request
        is_valid, error_msg = validate_request(data)
        if not is_valid:
            log_message("WARNING", f"Invalid request: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        user_message = data.get('message', '').strip()
        client_history = data.get('history', [])
        
        log_message("INFO", f"User message: {user_message[:50]}...")
        
        # Build conversation messages array
        messages = [SYSTEM_PROMPT]
        
        # Add conversation history (excluding the current user message already in frontend)
        for turn in client_history[:-1]:
            if turn.get('role') in ('user', 'assistant'):
                messages.append({
                    'role': turn['role'],
                    'content': turn['content']
                })
        
        # Append current user message
        messages.append({'role': 'user', 'content': user_message})
        
        try:
            log_message("INFO", "Calling Sarvam AI API...")
            
            response = client.chat.completions(
                messages=messages,
                model="sarvam-30b",
                temperature=0.8,
                reasoning_effort="medium"
            )
            
            assistant_text = response.choices[0].message.content
            cleaned_response = clean_response(assistant_text)
            
            log_message("INFO", f"Response generated: {cleaned_response[:50]}...")
            
            return jsonify({
                'response': cleaned_response,
                'success': True,
                'timestamp': get_timestamp()
            }), 200
        
        except AttributeError as ae:
            log_message("ERROR", f"API response format error: {str(ae)}")
            return jsonify({
                'error': 'Unexpected response format from AI service',
                'details': str(ae)
            }), 500
        
        except Exception as sarvam_error:
            log_message("ERROR", f"Sarvam AI error: {str(sarvam_error)}")
            return jsonify({
                'error': 'Failed to get response from AI service',
                'details': str(sarvam_error)
            }), 502
    
    except json.JSONDecodeError:
        log_message("ERROR", "Invalid JSON in request body")
        return jsonify({'error': 'Invalid JSON format'}), 400
    
    except Exception as e:
        log_message("ERROR", f"Unexpected server error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/info', methods=['GET'])
def info():
    """Return server information."""
    return jsonify({
        'name': 'BTechX AI Server',
        'version': '2.0',
        'model': 'sarvam-30b',
        'endpoints': [
            '/health',
            '/info',
            '/chat'
        ],
        'features': [
            'Multi-turn conversation support',
            'Markdown cleaning',
            'Request validation',
            'Error handling',
            'Comprehensive logging'
        ]
    }), 200

# ─ ERROR HANDLERS ─
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    log_message("WARNING", f"404 error: {request.path}")
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    log_message("WARNING", f"405 error: {request.method} {request.path}")
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    log_message("ERROR", f"500 error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

# ─ BEFORE/AFTER HANDLERS ─
@app.before_request
def log_request():
    """Log incoming requests."""
    log_message("INFO", f"Request: {request.method} {request.path}")

@app.after_request
def log_response(response):
    """Log response status."""
    log_message("INFO", f"Response: {response.status_code}")
    return response

port = int(os.environ.get("PORT", 5000))
# ─ APPLICATION ENTRY POINT ─
if __name__ == '__main__':
    log_message("INFO", "=" * 60)
    log_message("INFO", "BTechX AI Server v2.0")
    log_message("INFO", "Powered by Sarvam AI (sarvam-30b)")
    log_message("INFO", "=" * 60)
    log_message("INFO", "Starting server on http://0.0.0.0:{port}")
    log_message("INFO", "Health check: GET http://0.0.0.0:{port}/health")
    log_message("INFO", "Chat endpoint: POST http://0.0.0.0:{port}/chat")
    log_message("INFO", "=" * 60)
    
    try:
        app.run(debug=False, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        log_message("INFO", "Server shutdown initiated")
    except Exception as e:
        log_message("ERROR", f"Server failed to start: {str(e)}")
