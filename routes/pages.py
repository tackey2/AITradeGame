"""
Page Routes Blueprint
Handles HTML page rendering.
"""
from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def index():
    """Default route - Enhanced dashboard"""
    return render_template('enhanced.html')


@pages_bp.route('/enhanced')
def enhanced():
    """Enhanced dashboard (alias for /)"""
    return render_template('enhanced.html')


@pages_bp.route('/classic')
def classic():
    """Classic view (legacy)"""
    return render_template('index.html')


@pages_bp.route('/test_ui_debug.html')
def test_ui_debug():
    with open('test_ui_debug.html', 'r') as f:
        return f.read()


@pages_bp.route('/test-profiles')
def test_profiles():
    return render_template('test_profiles.html')


@pages_bp.route('/reports')
def reports():
    """Reports page"""
    return render_template('reports.html')
