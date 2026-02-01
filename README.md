# Accident Hotspot Alert System

A comprehensive web application that predicts traffic accident hotspots using PyTorch Geometric GNN and sends real-time alert messages to users in high-risk areas.

## Features

- **🗺️ Interactive Map**: Visual interface with real-time hotspot visualization
- **📍 Location-based Detection**: Find accident hotspots within a specified radius
- **📱 SMS Alerts**: Automatic warning messages sent to registered users
- **🔍 Risk Analysis**: Detailed risk scoring and distance calculations
- **👥 User Management**: Register phone numbers for alert notifications
- **🎯 Targeted Alerts**: Send alerts only to users in affected areas

## System Architecture

### Backend (Flask)
- **PyTorch GNN Model**: Accident prediction using Graph Attention Networks
- **Location Services**: Geospatial calculations using geopy
- **Database**: SQLite for user registration and alert logging
- **SMS Integration**: Twilio API for message delivery

### Frontend
- **Responsive Design**: Bootstrap 5 for mobile-friendly interface
- **Interactive Maps**: Leaflet.js for geographic visualization
- **Real-time Updates**: Dynamic hotspot detection and display

## Installation

### Prerequisites
- Python 3.8+
- Node.js (for frontend dependencies)
- Twilio account (for SMS functionality)

### Setup Instructions

1. **Clone the repository**
```bash
git clone <repository-url>
cd accident-alert-system
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Download the Chicago traffic dataset**
```bash
wget https://github.com/baixianghuang/travel/raw/main/TAP-city/chicago_il.npz
```

4. **Configure environment variables**
```bash
# For Windows
set TWILIO_ACCOUNT_SID=your_account_sid
set TWILIO_AUTH_TOKEN=your_auth_token
set TWILIO_PHONE_NUMBER=your_twilio_phone_number

# For Linux/Mac
export TWILIO_ACCOUNT_SID=your_account_sid
export TWILIO_AUTH_TOKEN=your_auth_token
export TWILIO_PHONE_NUMBER=your_twilio_phone_number
```

5. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### 1. Check Hotspots
- Enter latitude/longitude or use current location
- Adjust search radius (0.5-5 km)
- Click "Check Hotspots" to analyze the area
- View results on the map and in the analysis panel

### 2. Register for Alerts
- Enter your phone number (with country code)
- Optionally use current location for alerts
- Click "Register for Alerts"

### 3. Send Alert Messages
- Select a location with detected hotspots
- Click "Send Alerts" to notify all registered users in the area
- Users receive SMS: "⚠️ High accident-risk area near your location. Drive carefully."

## API Endpoints

### POST `/api/check_hotspots`
Check for accident hotspots near a location.

**Request:**
```json
{
    "latitude": 41.8781,
    "longitude": -87.6298,
    "radius_km": 2
}
```

**Response:**
```json
{
    "location": {"lat": 41.8781, "lng": -87.6298},
    "radius_km": 2,
    "hotspots_found": 3,
    "hotspots": [
        {
            "lat": 41.8785,
            "lng": -87.6295,
            "risk_score": 0.85,
            "distance_km": 0.5
        }
    ]
}
```

### POST `/api/register_user`
Register a user for alert notifications.

**Request:**
```json
{
    "phone_number": "+1234567890",
    "latitude": 41.8781,
    "longitude": -87.6298
}
```

### POST `/api/send_alerts`
Send alert messages to users in a specific area.

**Request:**
```json
{
    "latitude": 41.8781,
    "longitude": -87.6298,
    "radius_km": 2
}
```

### GET `/api/hotspots`
Get all accident hotspots for map visualization.

**Response:**
```json
{
    "hotspots": [
        {
            "lat": 41.8785,
            "lng": -87.6295,
            "risk_score": 0.85
        }
    ]
}
```

## Database Schema

### Users Table
- `id`: Primary key
- `phone_number`: User's phone number (unique)
- `latitude`: User's latitude for location-based alerts
- `longitude`: User's longitude for location-based alerts
- `created_at`: Registration timestamp

### Alerts_Sent Table
- `id`: Primary key
- `phone_number`: Recipient's phone number
- `message`: Alert message content
- `location_lat`: Alert location latitude
- `location_lng`: Alert location longitude
- `sent_at`: Alert timestamp

## Model Details

The system uses a Graph Attention Network (GAT) with the following architecture:
- **Input Layer**: 9 features (traffic data)
- **Hidden Layers**: 64 neurons with GATv2Conv
- **Output Layer**: Binary classification (accident risk)
- **Training**: 30 epochs with Adam optimizer

## Configuration

### Twilio Setup
1. Create a Twilio account at https://www.twilio.com
2. Get your Account SID and Auth Token
3. Purchase a phone number or use your trial number
4. Set the environment variables as shown in setup

### Customization
- Modify `radius_km` range in the frontend
- Adjust risk threshold in `AccidentAlertSystem.find_nearby_hotspots()`
- Customize alert message in `send_alerts()` function

## Security Considerations

- Phone numbers are validated with regex patterns
- SMS sending requires proper Twilio authentication
- Database uses parameterized queries to prevent SQL injection
- CORS is handled by Flask for secure API access

## Performance

- **Response Time**: < 2 seconds for hotspot detection
- **Scalability**: SQLite can handle thousands of users
- **Memory Usage**: Efficient geospatial calculations
- **SMS Rate**: Follows Twilio API limits (1 msg/second)

## Troubleshooting

### Common Issues

1. **Model not loading**: Ensure `chicago_il.npz` is in the correct directory
2. **SMS not sending**: Check Twilio credentials and phone number format
3. **Location not working**: Enable browser geolocation permissions
4. **Database errors**: Ensure write permissions for the application directory

### Logs
Check the console output for detailed error messages and debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For technical support or questions, please open an issue in the repository or contact the development team.
