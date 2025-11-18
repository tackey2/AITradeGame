"""
Provider API Blueprint
Handles API provider management endpoints.
"""
from flask import Blueprint, request, jsonify
import requests
from routes import app_context

providers_bp = Blueprint('providers', __name__)


@providers_bp.route('/api/providers', methods=['GET'])
def get_providers():
    """Get all API providers"""
    db = app_context['db']
    providers = db.get_all_providers()
    return jsonify(providers)


@providers_bp.route('/api/providers', methods=['POST'])
def add_provider():
    """Add new API provider"""
    db = app_context['db']
    data = request.json
    try:
        provider_id = db.add_provider(
            name=data['name'],
            api_url=data['api_url'],
            api_key=data['api_key'],
            models=data.get('models', '')
        )
        return jsonify({'id': provider_id, 'message': 'Provider added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@providers_bp.route('/api/providers/<int:provider_id>', methods=['PUT'])
def update_provider(provider_id):
    """Update API provider"""
    db = app_context['db']
    data = request.json
    try:
        db.update_provider(
            provider_id=provider_id,
            name=data['name'],
            api_url=data['api_url'],
            api_key=data['api_key'],
            models=data.get('models', '')
        )
        return jsonify({'message': 'Provider updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@providers_bp.route('/api/providers/<int:provider_id>', methods=['DELETE'])
def delete_provider(provider_id):
    """Delete API provider"""
    db = app_context['db']
    try:
        db.delete_provider(provider_id)
        return jsonify({'message': 'Provider deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@providers_bp.route('/api/providers/models', methods=['POST'])
def fetch_provider_models():
    """Fetch available models from provider's API"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')

    if not api_url or not api_key:
        return jsonify({'error': 'API URL and key are required'}), 400

    try:
        models = []

        # Try to detect provider type and call appropriate API
        if 'openai.com' in api_url.lower():
            # OpenAI API call
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.get(f'{api_url}/models', headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                models = [m['id'] for m in result.get('data', []) if 'gpt' in m['id'].lower()]
        elif 'deepseek' in api_url.lower():
            # DeepSeek API
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.get(f'{api_url}/models', headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                models = [m['id'] for m in result.get('data', [])]
        elif 'openrouter.ai' in api_url.lower():
            # OpenRouter API - fetch available models
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.get('https://openrouter.ai/api/v1/models', headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                models = [m['id'] for m in result.get('data', [])]
        else:
            # Generic OpenAI-compatible API
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            # Try standard /models endpoint
            try:
                response = requests.get(f'{api_url}/models', headers=headers, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if 'data' in result:
                        models = [m['id'] for m in result.get('data', [])]
                    else:
                        # Fallback to common model names
                        models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
                else:
                    # Fallback to common model names
                    models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
            except:
                # Fallback to common model names
                models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']

        return jsonify({'models': models})
    except Exception as e:
        print(f"[ERROR] Fetch models failed: {e}")
        return jsonify({'error': f'Failed to fetch models: {str(e)}'}), 500
