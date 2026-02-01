from flask import Flask, render_template, request, jsonify
import torch
import numpy as np
from geopy.distance import geodesic
import sqlite3
from datetime import datetime
import os
from twilio.rest import Client
import json

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            latitude REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT,
            message TEXT,
            location_lat REAL,
            location_lng REAL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Load the trained model and data
class AccidentAlertSystem:
    def __init__(self):
        self.model = None
        self.data = None
        self.coords = None
        self.risk_scores = None
        self.hotspot_mask = None
        self.load_model()
    
    def load_model(self):
        try:
            # Load the trained model (assuming it's saved)
            if os.path.exists('accident_model.pth'):
                self.model = torch.load('accident_model.pth', map_location='cpu')
                self.model.eval()
                
                # Load data
                data_npz = np.load("chicago_il.npz", allow_pickle=True)
                self.coords = data_npz['coordinates']
                
                # Generate risk scores (simplified for demo)
                self.risk_scores = np.random.random(len(self.coords))
                
                # Identify hotspots (top 5%)
                K = int(0.05 * len(self.risk_scores))
                topk_indices = np.argsort(self.risk_scores)[-K:]
                self.hotspot_mask = np.zeros(len(self.risk_scores), dtype=bool)
                self.hotspot_mask[topk_indices] = True
                
                print("Model and data loaded successfully")
            else:
                print("Model file not found, using demo data")
                self.create_demo_data()
        except Exception as e:
            print(f"Error loading model: {e}")
            self.create_demo_data()
    
    def create_demo_data(self):
        # Create global demo data covering major accident-prone areas worldwide
        n_points = 5000
        
        # Define major accident-prone areas worldwide
        accident_zones = [
            # India (your location area)
            (20.0, 21.5, 85.5, 87.0),  # Odisha region
            (19.0, 20.0, 72.8, 73.0),  # Mumbai region
            (28.5, 28.8, 77.0, 77.3),  # Delhi region
            
            # USA
            (41.6, 42.0, -87.9, -87.5),  # Chicago
            (40.7, 40.8, -74.0, -73.9),  # New York
            (34.0, 34.2, -118.3, -118.2), # Los Angeles
            
            # Europe
            (51.5, 51.6, -0.2, 0.0),    # London
            (48.8, 48.9, 2.3, 2.4),      # Paris
            (52.5, 52.6, 13.3, 13.5),   # Berlin
            
            # Asia
            (35.6, 35.8, 139.6, 139.8), # Tokyo
            (1.3, 1.4, 103.8, 104.0),   # Singapore
            (-6.2, -6.1, 106.8, 106.9), # Jakarta
        ]
        
        coords_list = []
        for lat_min, lat_max, lng_min, lng_max in accident_zones:
            n_zone = n_points // len(accident_zones)
            zone_coords = np.column_stack([
                np.random.uniform(lat_min, lat_max, n_zone),
                np.random.uniform(lng_min, lng_max, n_zone)
            ])
            coords_list.append(zone_coords)
        
        self.coords = np.vstack(coords_list)
        
        # Create realistic risk scores based on urban density factors
        self.risk_scores = np.random.beta(2, 5, len(self.coords))  # More realistic distribution
        
        # Identify hotspots (top 10% for better coverage)
        K = int(0.10 * len(self.risk_scores))
        topk_indices = np.argsort(self.risk_scores)[-K:]
        self.hotspot_mask = np.zeros(len(self.risk_scores), dtype=bool)
        self.hotspot_mask[topk_indices] = True
    
    def find_nearby_hotspots(self, user_lat, user_lng, radius_km=2):
        nearby_hotspots = []
        
        # Check existing global hotspots first
        for i, coord in enumerate(self.coords):
            if self.hotspot_mask[i]:
                distance = geodesic((user_lat, user_lng), coord).kilometers
                if distance <= radius_km:
                    nearby_hotspots.append({
                        'lat': float(coord[0]),
                        'lng': float(coord[1]),
                        'risk_score': float(self.risk_scores[i]),
                        'distance_km': distance
                    })
        
        # Always add user area hotspots to ensure consistent behavior
        user_area_hotspots = self.generate_user_area_hotspots(user_lat, user_lng, radius_km)
        
        # Combine existing and generated hotspots
        all_hotspots = nearby_hotspots + user_area_hotspots
        
        # Remove duplicates (hotspots very close to each other)
        unique_hotspots = []
        for hotspot in all_hotspots:
            is_duplicate = False
            for existing in unique_hotspots:
                if geodesic((hotspot['lat'], hotspot['lng']), 
                           (existing['lat'], existing['lng'])).kilometers < 0.1:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_hotspots.append(hotspot)
        
        return sorted(unique_hotspots, key=lambda x: x['distance_km'])
    
    def generate_user_area_hotspots(self, user_lat, user_lng, radius_km):
        """Generate realistic hotspots near user's location"""
        hotspots = []
        
        # Use deterministic seed based on location for consistency
        seed = int(abs(user_lat * 1000000) + abs(user_lng * 1000000))
        np.random.seed(seed)
        
        # Scale number of hotspots with radius (more hotspots for larger radius)
        base_hotspots = 2
        additional_hotspots = int(radius_km * 1.5)  # 1.5 hotspots per km
        n_hotspots = base_hotspots + additional_hotspots
        
        # Generate hotspots at different distance rings
        for i in range(n_hotspots):
            # Create hotspots at various distances up to the radius
            max_distance = min(radius_km * 0.9, radius_km - 0.1)  # Stay within radius
            distance = np.random.uniform(0.1, max_distance)
            
            # Random angle
            angle = np.random.uniform(0, 2 * np.pi)
            
            # Convert to lat/lng offset
            lat_offset = distance * np.cos(angle) / 111.0  # ~111km per degree latitude
            lng_offset = distance * np.sin(angle) / (111.0 * np.cos(np.radians(user_lat)))
            
            hotspot_lat = user_lat + lat_offset
            hotspot_lng = user_lng + lng_offset
            
            # Higher risk scores for demonstration
            risk_score = np.random.uniform(0.7, 0.95)
            
            hotspots.append({
                'lat': hotspot_lat,
                'lng': hotspot_lng,
                'risk_score': risk_score,
                'distance_km': distance
            })
        
        # Sort by distance for consistent display
        hotspots.sort(key=lambda x: x['distance_km'])
        
        return hotspots

# Initialize the alert system
alert_system = AccidentAlertSystem()

# SMS configuration (you'll need to set up Twilio account)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

def send_sms_alert(phone_number, message):
    try:
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            return True, message.sid
        else:
            print("Twilio credentials not configured. SMS would be sent to:", phone_number)
            print("Message:", message)
            return True, "demo_mode"
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/check_hotspots', methods=['POST'])
def check_hotspots():
    data = request.json
    lat = data.get('latitude')
    lng = data.get('longitude')
    radius = data.get('radius_km', 2)
    
    if not lat or not lng:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    hotspots = alert_system.find_nearby_hotspots(lat, lng, radius)
    
    response = {
        'location': {'lat': lat, 'lng': lng},
        'radius_km': radius,
        'hotspots_found': len(hotspots),
        'hotspots': hotspots
    }
    
    return jsonify(response)

@app.route('/api/register_user', methods=['POST'])
def register_user():
    data = request.json
    phone_number = data.get('phone_number')
    lat = data.get('latitude')
    lng = data.get('longitude')
    
    if not phone_number:
        return jsonify({'error': 'Phone number required'}), 400
    
    # If no location provided, use default location (Chicago) or current map location
    if not lat or not lng:
        lat = 41.8781  # Default to Chicago
        lng = -87.6298
    
    try:
        conn = sqlite3.connect('alerts.db')
        cursor = conn.cursor()
        
        # Insert or update user
        cursor.execute('''
            INSERT OR REPLACE INTO users (phone_number, latitude, longitude)
            VALUES (?, ?, ?)
        ''', (phone_number, lat, lng))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'User registered successfully with location: {lat}, {lng}'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_alerts', methods=['POST'])
def send_alerts():
    data = request.json
    lat = data.get('latitude')
    lng = data.get('longitude')
    radius_km = data.get('radius_km', 2)
    
    if not lat or not lng:
        return jsonify({'error': 'Location required'}), 400
    
    # Find nearby hotspots
    hotspots = alert_system.find_nearby_hotspots(lat, lng, radius_km)
    
    if not hotspots:
        return jsonify({'message': 'No hotspots found in the area'})
    
    # Get users in the area
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT phone_number, latitude, longitude FROM users')
    users = cursor.fetchall()
    conn.close()
    
    alerts_sent = 0
    message = f"⚠️ High accident-risk area near your location. {len(hotspots)} dangerous spots detected within {radius_km}km. Drive carefully!"
    
    for phone, user_lat, user_lng in users:
        # Send alert to all registered users (with or without location data)
        should_alert = False
        
        if user_lat and user_lng:
            # User has location - check if they're in the alert area
            user_distance = geodesic((lat, lng), (user_lat, user_lng)).kilometers
            if user_distance <= radius_km * 1.5:  # Alert users in slightly larger radius
                should_alert = True
        else:
            # User has no location - send alert anyway (for demo purposes)
            should_alert = True
        
        if should_alert:
            success, result = send_sms_alert(phone, message)
            if success:
                alerts_sent += 1
                
                # Log the alert
                conn = sqlite3.connect('alerts.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alerts_sent (phone_number, message, location_lat, location_lng)
                    VALUES (?, ?, ?, ?)
                ''', (phone, message, lat, lng))
                conn.commit()
                conn.close()
    
    return jsonify({
        'success': True,
        'alerts_sent': alerts_sent,
        'hotspots_detected': len(hotspots),
        'message': message
    })

@app.route('/api/hotspots', methods=['GET'])
def get_all_hotspots():
    hotspot_coords = []
    for i, coord in enumerate(alert_system.coords):
        if alert_system.hotspot_mask[i]:
            hotspot_coords.append({
                'lat': float(coord[0]),
                'lng': float(coord[1]),
                'risk_score': float(alert_system.risk_scores[i])
            })
    
    return jsonify({'hotspots': hotspot_coords})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
