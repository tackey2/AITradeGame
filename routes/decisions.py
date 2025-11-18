"""
Decision management routes blueprint
Handles pending decisions, decision history, and approval/rejection endpoints
"""
from flask import Blueprint, request, jsonify
import json

# Import trading components
from ai_trader import AITrader
from risk_manager import RiskManager
from notifier import Notifier
from explainer import AIExplainer
from trading_modes import TradingExecutor

# Create blueprint
decisions_bp = Blueprint('decisions', __name__, url_prefix='/api')

# Shared resources (injected via init_app)
_enhanced_db = None
_trading_executors = None
_risk_managers = None
_notifiers = None
_explainers = None


def init_app(enhanced_db, trading_executors, risk_managers=None, notifiers=None, explainers=None):
    """
    Initialize blueprint with shared resources

    Args:
        enhanced_db: EnhancedDatabase instance
        trading_executors: Dict of model_id -> TradingExecutor
        risk_managers: Dict of model_id -> RiskManager (optional)
        notifiers: Dict of model_id -> Notifier (optional)
        explainers: Dict of model_id -> AIExplainer (optional)
    """
    global _enhanced_db, _trading_executors, _risk_managers, _notifiers, _explainers

    _enhanced_db = enhanced_db
    _trading_executors = trading_executors
    _risk_managers = risk_managers if risk_managers is not None else {}
    _notifiers = notifiers if notifiers is not None else {}
    _explainers = explainers if explainers is not None else {}


# ============ HELPER FUNCTIONS ============

def init_enhanced_components(model_id):
    """Initialize risk manager, notifier, explainer, and executor for a model"""
    if model_id not in _risk_managers:
        _risk_managers[model_id] = RiskManager(_enhanced_db)

    if model_id not in _notifiers:
        _notifiers[model_id] = Notifier(_enhanced_db)

    if model_id not in _explainers:
        # Get model to access AI configuration
        model = _enhanced_db.get_model(model_id)
        provider = _enhanced_db.get_provider(model['provider_id'])

        ai_trader = AITrader(
            api_key=provider['api_key'],
            api_url=provider['api_url'],
            model_name=model['model_name']
        )
        _explainers[model_id] = AIExplainer(ai_trader)

    if model_id not in _trading_executors:
        # Create executor with all components
        _trading_executors[model_id] = TradingExecutor(
            db=_enhanced_db,
            risk_manager=_risk_managers[model_id],
            notifier=_notifiers[model_id],
            explainer=_explainers[model_id]
        )


# ============ ROUTES ============

@decisions_bp.route('/pending-decisions', methods=['GET'])
def get_all_pending_decisions():
    """Get all pending decisions across all models"""
    try:
        model_id = request.args.get('model_id', type=int)

        if model_id:
            decisions = _enhanced_db.get_pending_decisions(model_id, status='pending')
        else:
            # Get all pending decisions
            conn = _enhanced_db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM pending_decisions
                WHERE status = 'pending'
                ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            conn.close()

            decisions = []
            for row in rows:
                data = dict(row)
                data['decision_data'] = json.loads(data['decision_data'])
                if data['explanation_data']:
                    data['explanation_data'] = json.loads(data['explanation_data'])
                decisions.append(data)

        return jsonify(decisions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@decisions_bp.route('/decision-history', methods=['GET'])
def get_decision_history():
    """Get decision history with filtering options"""
    try:
        model_id = request.args.get('model_id', type=int)
        status_filter = request.args.get('status', None)  # 'pending', 'approved', 'rejected', 'expired', or None for all
        limit = request.args.get('limit', 100, type=int)

        conn = _enhanced_db.get_connection()
        cursor = conn.cursor()

        # Build query with filters
        query = 'SELECT * FROM pending_decisions WHERE 1=1'
        params = []

        if model_id:
            query += ' AND model_id = ?'
            params.append(model_id)

        if status_filter:
            query += ' AND status = ?'
            params.append(status_filter)

        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        decisions = []
        for row in rows:
            data = dict(row)
            data['decision_data'] = json.loads(data['decision_data'])
            if data['explanation_data']:
                data['explanation_data'] = json.loads(data['explanation_data'])
            decisions.append(data)

        return jsonify(decisions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@decisions_bp.route('/pending-decisions/<int:decision_id>/approve', methods=['POST'])
def approve_pending_decision(decision_id):
    """Approve a pending decision"""
    try:
        data = request.json or {}
        modified = data.get('modified', False)
        modifications = data.get('modifications', None)

        # Initialize components if needed
        decisions = _enhanced_db.get_pending_decisions(model_id=None, status='pending')
        decision = next((d for d in decisions if d['id'] == decision_id), None)

        if not decision:
            return jsonify({'error': 'Decision not found'}), 404

        model_id = decision['model_id']
        init_enhanced_components(model_id)

        # Execute approval
        result = _trading_executors[model_id].approve_decision(
            decision_id=decision_id,
            modified=modified,
            modifications=modifications
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@decisions_bp.route('/pending-decisions/<int:decision_id>/reject', methods=['POST'])
def reject_pending_decision(decision_id):
    """Reject a pending decision"""
    try:
        data = request.json or {}
        reason = data.get('reason', 'User rejected')

        # Initialize components if needed
        decisions = _enhanced_db.get_pending_decisions(model_id=None, status='pending')
        decision = next((d for d in decisions if d['id'] == decision_id), None)

        if not decision:
            return jsonify({'error': 'Decision not found'}), 404

        model_id = decision['model_id']
        init_enhanced_components(model_id)

        # Execute rejection
        result = _trading_executors[model_id].reject_decision(
            decision_id=decision_id,
            reason=reason
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
