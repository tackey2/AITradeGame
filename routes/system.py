"""
System routes for settings, version, updates, and leaderboard.
"""
from flask import Blueprint, request, jsonify
import re

from version import __version__, __github_owner__, __repo__, GITHUB_REPO_URL, LATEST_RELEASE_URL

system_bp = Blueprint('system', __name__, url_prefix='/api')

# Shared resources will be injected via init_app
db = None
enhanced_db = None
market_fetcher = None
auto_trading_flag = None


def init_app(database, enhanced_database, market_fetcher_instance, auto_trading):
    """Initialize blueprint with shared resources"""
    global db, enhanced_db, market_fetcher, auto_trading_flag
    db = database
    enhanced_db = enhanced_database
    market_fetcher = market_fetcher_instance
    auto_trading_flag = auto_trading


# ============ Helper Functions ============

def compare_versions(version1, version2):
    """Compare two version strings.

    Returns:
        1 if version1 > version2
        0 if version1 == version2
        -1 if version1 < version2
    """
    def normalize(v):
        # Extract numeric parts from version string
        parts = re.findall(r'\d+', v)
        # Pad with zeros to make them comparable
        return [int(p) for p in parts]

    v1_parts = normalize(version1)
    v2_parts = normalize(version2)

    # Pad shorter version with zeros
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))

    # Compare
    if v1_parts > v2_parts:
        return 1
    elif v1_parts < v2_parts:
        return -1
    else:
        return 0


# ============ Leaderboard API ============

@system_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    models = db.get_all_models()
    leaderboard = []

    prices_data = market_fetcher.get_current_prices(['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
    current_prices = {coin: prices_data[coin]['price'] for coin in prices_data}

    for model in models:
        portfolio = db.get_portfolio(model['id'], current_prices)
        account_value = portfolio.get('total_value', model['initial_capital'])
        returns = ((account_value - model['initial_capital']) / model['initial_capital']) * 100

        leaderboard.append({
            'model_id': model['id'],
            'model_name': model['name'],
            'account_value': account_value,
            'returns': returns,
            'initial_capital': model['initial_capital']
        })

    leaderboard.sort(key=lambda x: x['returns'], reverse=True)
    return jsonify(leaderboard)


# ============ Settings API ============

@system_bp.route('/settings', methods=['GET'])
def get_settings():
    """Get system settings"""
    try:
        settings = db.get_settings()
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/settings', methods=['PUT'])
def update_settings():
    """Update system settings"""
    try:
        data = request.json
        trading_frequency_minutes = int(data.get('trading_frequency_minutes', 60))
        trading_fee_rate = float(data.get('trading_fee_rate', 0.001))

        success = db.update_settings(trading_frequency_minutes, trading_fee_rate)

        if success:
            return jsonify({'success': True, 'message': 'Settings updated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update settings'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ Version API ============

@system_bp.route('/version', methods=['GET'])
def get_version():
    """Get current version information"""
    return jsonify({
        'current_version': __version__,
        'github_repo': GITHUB_REPO_URL,
        'latest_release_url': LATEST_RELEASE_URL
    })

@system_bp.route('/check-update', methods=['GET'])
def check_update():
    """Check for GitHub updates"""
    try:
        import requests

        # Get latest release from GitHub
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AITradeGame/1.0'
        }

        # Try to get latest release
        try:
            response = requests.get(
                f"https://api.github.com/repos/{__github_owner__}/{__repo__}/releases/latest",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get('tag_name', '').lstrip('v')
                release_url = release_data.get('html_url', '')
                release_notes = release_data.get('body', '')

                # Compare versions
                is_update_available = compare_versions(latest_version, __version__) > 0

                return jsonify({
                    'update_available': is_update_available,
                    'current_version': __version__,
                    'latest_version': latest_version,
                    'release_url': release_url,
                    'release_notes': release_notes,
                    'repo_url': GITHUB_REPO_URL
                })
            else:
                # If API fails, still return current version info
                return jsonify({
                    'update_available': False,
                    'current_version': __version__,
                    'error': 'Could not check for updates'
                })
        except Exception as e:
            print(f"[WARN] GitHub API error: {e}")
            return jsonify({
                'update_available': False,
                'current_version': __version__,
                'error': 'Network error checking updates'
            })

    except Exception as e:
        print(f"[ERROR] Check update failed: {e}")
        return jsonify({
            'update_available': False,
            'current_version': __version__,
            'error': str(e)
        }), 500


# ============ Graduation Settings API ============

@system_bp.route('/graduation-settings', methods=['GET'])
def get_graduation_settings_api():
    """Get graduation criteria settings"""
    try:
        settings = db.get_graduation_settings()
        return jsonify(settings if settings else {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/graduation-settings', methods=['POST'])
def update_graduation_settings_api():
    """Update graduation criteria settings"""
    try:
        settings = request.json
        db.update_graduation_settings(settings)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ Benchmark Settings API ============

@system_bp.route('/benchmark-settings', methods=['GET'])
def get_benchmark_settings_api():
    """Get benchmark settings"""
    try:
        settings = db.get_benchmark_settings()
        return jsonify(settings if settings else {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/benchmark-settings', methods=['POST'])
def update_benchmark_settings_api():
    """Update benchmark settings"""
    try:
        settings = request.json
        db.update_benchmark_settings(settings)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ Cost Tracking Settings API ============

@system_bp.route('/cost-tracking-settings', methods=['GET'])
def get_cost_tracking_settings_api():
    """Get cost tracking settings"""
    try:
        settings = db.get_cost_tracking_settings()
        return jsonify(settings if settings else {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_bp.route('/cost-tracking-settings', methods=['POST'])
def update_cost_tracking_settings_api():
    """Update cost tracking settings"""
    try:
        settings = request.json
        db.update_cost_tracking_settings(settings)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
