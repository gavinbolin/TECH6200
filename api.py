from flask import Blueprint, jsonify, request, session
from models import db, decrypt, _find_inventory_item, list_inventory
import functools

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def api_login_required(f):
    """API-specific login required decorator that returns JSON error instead of redirect"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

@api_bp.route('/inventory', methods=['GET'])
@api_login_required
def get_inventory():
    """Get all inventory items for the authenticated user"""
    try:
        user_id = session['user_id']
        items = list_inventory(user_id)
        return jsonify({
            'success': True,
            'count': len(items),
            'items': items
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve inventory'
        }), 500

@api_bp.route('/inventory/<item_name>', methods=['GET'])
@api_login_required
def get_inventory_item(item_name):
    """Get a specific inventory item for the authenticated user"""
    try:
        user_id = session['user_id']
        item = _find_inventory_item(item_name, user_id)

        if item is None:
            return jsonify({
                'success': False,
                'error': f'Item "{item_name}" not found'
            }), 404

        return jsonify({
            'success': True,
            'item': {
                'name': decrypt(item.name),
                'quantity': decrypt(item.quantity)
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve item'
        }), 500