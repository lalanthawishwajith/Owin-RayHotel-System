# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ============ CONFIG ============
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# ============ DATA ============
orders = []
order_counter = 1

# Menu Items
MENU_ITEMS = [
    # Rice
    {"id": "R01", "name": "Chicken Fried Rice", "category": "meal", "price": 1200},
    {"id": "R02", "name": "Vegetable Fried Rice", "category": "meal", "price": 800},
    {"id": "R03", "name": "Seafood Fried Rice", "category": "meal", "price": 1800},
    {"id": "R04", "name": "Egg Fried Rice", "category": "meal", "price": 900},
    {"id": "R05", "name": "Prawn Fried Rice", "category": "meal", "price": 1600},
    # Noodles
    {"id": "N01", "name": "Chicken Noodles", "category": "meal", "price": 1200},
    {"id": "N02", "name": "Egg Noodles", "category": "meal", "price": 900},
    {"id": "N03", "name": "Seafood Noodles", "category": "meal", "price": 1800},
    {"id": "N04", "name": "Vegetable Noodles", "category": "meal", "price": 750},
    # Curries
    {"id": "C01", "name": "Chicken Curry", "category": "meal", "price": 1500},
    {"id": "C02", "name": "Fish Curry", "category": "meal", "price": 1800},
    {"id": "C03", "name": "Dhal Curry", "category": "meal", "price": 600},
    {"id": "C04", "name": "Prawn Curry", "category": "meal", "price": 2200},
    {"id": "C05", "name": "Beef Curry", "category": "meal", "price": 1600},
    {"id": "C06", "name": "Vegetable Curry", "category": "meal", "price": 700},
    {"id": "C07", "name": "Devilled Chicken", "category": "meal", "price": 1700},
    {"id": "C08", "name": "Cashew Curry", "category": "meal", "price": 1200},
    # Soft Drinks
    {"id": "S01", "name": "Fresh Lime Soda", "category": "soft_drink", "price": 600},
    {"id": "S02", "name": "Coca Cola", "category": "soft_drink", "price": 250},
    {"id": "S03", "name": "Sprite", "category": "soft_drink", "price": 250},
    {"id": "S04", "name": "Orange Juice", "category": "soft_drink", "price": 500},
    {"id": "S05", "name": "Mango Juice", "category": "soft_drink", "price": 550},
    {"id": "S06", "name": "Water Bottle", "category": "soft_drink", "price": 150},
    {"id": "S07", "name": "Hot Tea", "category": "soft_drink", "price": 200},
    {"id": "S08", "name": "Coffee", "category": "soft_drink", "price": 300},
    {"id": "S09", "name": "Milkshake", "category": "soft_drink", "price": 750},
]

# ============ API ENDPOINTS ============

@app.route('/')
def home():
    return jsonify({
        "message": "🏨 Hotel Management System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "menu": "/api/menu",
            "orders": "/api/orders",
            "kitchen": "/api/kitchen/orders",
            "dashboard": "/api/dashboard"
        }
    })

@app.route('/api/menu', methods=['GET'])
def get_menu():
    return jsonify(MENU_ITEMS)

@app.route('/api/orders', methods=['POST'])
def place_order():
    global order_counter
    
    data = request.get_json()
    
    order = {
        "id": order_counter,
        "order_type": data.get('order_type', 'table'),
        "table_number": data.get('table_number', '0'),
        "customer_name": data.get('customer_name', 'Guest'),
        "items": data.get('items', []),
        "total_amount": data.get('total_amount', 0),
        "status": "pending",
        "order_time": datetime.now().isoformat(),
        "estimated_time": 20
    }
    
    orders.append(order)
    order_counter += 1
    
    # Real-time update to Kitchen & Office
    socketio.emit('new_order', {'order': order})
    
    return jsonify({
        "success": True,
        "order_id": order['id'],
        "message": f"Order #{order['id']} placed successfully!"
    }), 201

@app.route('/api/orders', methods=['GET'])
def get_all_orders():
    return jsonify(orders)

@app.route('/api/kitchen/orders', methods=['GET'])
def get_kitchen_orders():
    pending = [o for o in orders if o['status'] in ['pending', 'cooking', 'ready']]
    # Sort by time (FIFO)
    pending.sort(key=lambda x: x['order_time'])
    return jsonify(pending)

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    
    for order in orders:
        if order['id'] == order_id:
            order['status'] = new_status
            socketio.emit('order_update', {
                'order_id': order_id,
                'status': new_status
            })
            return jsonify({
                "success": True,
                "message": f"Order #{order_id} status updated to {new_status}"
            })
    
    return jsonify({"error": "Order not found"}), 404

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    total = len(orders)
    pending = len([o for o in orders if o['status'] in ['pending', 'cooking']])
    cooking = len([o for o in orders if o['status'] == 'cooking'])
    ready = len([o for o in orders if o['status'] == 'ready'])
    served = len([o for o in orders if o['status'] == 'served'])
    total_sales = sum([o.get('total_amount', 0) for o in orders if o['status'] == 'served'])
    
    return jsonify({
        "total_orders": total,
        "pending_orders": pending,
        "cooking_orders": cooking,
        "ready_orders": ready,
        "served_orders": served,
        "total_sales": total_sales,
        "recent_orders": orders[-10:]
    })

# ============ WEBSOCKET EVENTS ============

@socketio.on('connect')
def handle_connect():
    print('✅ Client connected')
    emit('connected', {'message': 'Connected to server!'})

@socketio.on('disconnect')
def handle_disconnect():
    print('❌ Client disconnected')

# ============ MAIN ============

if __name__ == '__main__':
    print("=" * 50)
    print("🏨 Hotel Management System API")
    print(f"📡 Running on: http://localhost:5000")
    print("=" * 50)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)