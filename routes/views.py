"""
View routes for rendering HTML templates.
"""
from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def index():
    """Default route - Enhanced dashboard"""
    return render_template('enhanced.html')


@views_bp.route('/enhanced')
def enhanced():
    """Enhanced dashboard (alias for /)"""
    return render_template('enhanced.html')


@views_bp.route('/classic')
def classic():
    """Classic view (legacy)"""
    return render_template('index.html')


@views_bp.route('/test_ui_debug.html')
def test_ui_debug():
    with open('test_ui_debug.html', 'r') as f:
        return f.read()


@views_bp.route('/test-profiles')
def test_profiles():
    return render_template('test_profiles.html')
