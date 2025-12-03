"""
Simple REST API for LLM Agent.

This module provides a Flask-based REST API endpoint for querying
the NCAAFB database using natural language.
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Any

# Add current directory to path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(backend_dir))

try:
    from backend.llm_agent import LLMAgent
except ImportError:
    try:
        from llm_agent import LLMAgent
    except ImportError:
        # Try direct import from same directory
        import importlib.util
        spec = importlib.util.spec_from_file_location("llm_agent", os.path.join(backend_dir, "llm_agent.py"))
        llm_agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(llm_agent_module)
        LLMAgent = llm_agent_module.LLMAgent

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Global LLM agent instance
agent = None


def get_agent() -> LLMAgent:
    """Get or create LLM agent instance."""
    global agent
    if agent is None:
        try:
            agent = LLMAgent()
        except Exception as e:
            print(f"Error initializing LLM agent: {e}")
            raise
    return agent


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'NCAAFB LLM Agent API'
    })


@app.route('/query', methods=['POST'])
def query():
    """
    Query endpoint for natural language questions.
    
    Request body:
        {
            "question": "What teams are in the SEC conference?",
            "model": "gemini-1.5-pro",  # optional
            "max_results": 100  # optional
        }
    
    Response:
        {
            "answer": "Natural language answer...",
            "sql": "SELECT ...",
            "results": [...],
            "error": null
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'error': 'Missing required field: question'
            }), 400
        
        question = data['question']
        model = data.get('model', 'gemini-2.5-flash')
        max_results = data.get('max_results', 100)
        
        # Get agent (recreate if model changed)
        global agent
        if agent is None or agent.model_name != model:
            agent = LLMAgent(model_name=model)
        
        # Process query
        result = agent.query(question, max_results=max_results)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'answer': None,
            'sql': None,
            'results': None,
            'error': str(e)
        }), 500


@app.route('/schema', methods=['GET'])
def get_schema():
    """Get database schema information."""
    try:
        agent = get_agent()
        schema_info = agent.schema_info
        return jsonify(schema_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/test', methods=['GET'])
def test():
    """Test endpoint with a sample query."""
    try:
        agent = get_agent()
        result = agent.query("How many teams are in the database?")
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM Agent REST API')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("NCAAFB LLM Agent API")
    print("=" * 60)
    print(f"\nStarting server on http://{args.host}:{args.port}")
    print("\nEndpoints:")
    print("  GET  /health  - Health check")
    print("  POST /query   - Query the database")
    print("  GET  /schema  - Get database schema")
    print("  GET  /test    - Test with sample query")
    print("\nExample query:")
    print('  curl -X POST http://localhost:5000/query \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"question": "What teams are in the SEC?"}\'')
    print("\n" + "=" * 60 + "\n")
    
    app.run(host=args.host, port=args.port, debug=args.debug)

