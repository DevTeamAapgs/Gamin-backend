# 🎮 Gaming Platform Backend

A production-grade play-to-earn crypto gaming platform built with FastAPI, featuring real-time gameplay, secure authentication, and comprehensive analytics.

## 🚀 Features

### 🔐 Security
- **Triple-Layer Authentication**: JWT + AES encryption + Device fingerprinting
- **Secure Token Management**: Hourly rotating seeds, encrypted refresh tokens
- **Anti-Cheat System**: Replay analysis, pattern detection, speed hack detection
- **IP/Device Validation**: Multi-factor session security

### 🎯 Game Engine
- **Adaptive Difficulty**: Dynamic difficulty based on player performance
- **Multi-Game Support**: Pluggable architecture for different game types
- **Real-Time Gameplay**: WebSocket-based real-time communication
- **Fair Reward System**: Partial refunds based on completion percentage

### 📊 Analytics & Monitoring
- **Heatmap Generation**: Click frequency and interaction patterns
- **Player Analytics**: Performance tracking and behavior analysis
- **Platform Metrics**: Revenue tracking, user engagement, game statistics
- **Real-Time Monitoring**: Live dashboard with key metrics

### 🏗️ Architecture
- **Modular Design**: Pluggable game modules and services
- **Scalable Backend**: Async FastAPI with MongoDB and Redis
- **Admin Panel**: Full control over game economy and player management
- **Leaderboards**: Competitive ranking system

## 🛠️ Tech Stack

- **Backend**: FastAPI (Async Python)
- **Database**: MongoDB with Motor (async driver)
- **Cache**: Redis (optional)
- **Authentication**: JWT + AES encryption
- **Real-time**: WebSockets
- **Background Tasks**: Celery
- **API Documentation**: Swagger UI / ReDoc

## 📦 Installation

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Redis (optional)
- Docker (optional)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd gaming-platform-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
cp env.example .env
# Edit .env with your configuration
```

5. **Database Setup**
```bash
# Start MongoDB
mongod

# Start Redis (optional)
redis-server
```

6. **Run the application**
```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

## 🔧 Configuration

### Environment Variables

```env
# Database
MONGODB_URL=mongodb://localhost:27017/gaming_platform
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
AES_KEY=your-32-byte-aes-key-for-encryption

# Game Configuration
DEFAULT_GAME_TIMER=60
DEFAULT_ENTRY_COST=100
DEFAULT_REWARD_MULTIPLIER=1.5

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin-secure-password
```

## 📚 API Documentation

### Authentication Endpoints

#### Register Player
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "wallet_address": "0x1234567890abcdef...",
  "username": "player123",
  "email": "player@example.com",
  "device_fingerprint": "device_hash"
}
```

#### Login Player
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "wallet_address": "0x1234567890abcdef...",
  "device_fingerprint": "device_hash",
  "ip_address": "192.168.1.1"
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "encrypted_refresh_token"
}
```

### Game Endpoints

#### Start Game
```http
POST /api/v1/game/start
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "game_type": "color_match",
  "level": 1,
  "device_fingerprint": "device_hash"
}
```

#### Submit Game
```http
POST /api/v1/game/submit
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "game_id": "game_id",
  "completion_percentage": 85.5,
  "actions": [...],
  "mouse_movements": [...],
  "click_positions": [...],
  "timing_data": {...},
  "device_info": {...}
}
```

### Player Endpoints

#### Get Profile
```http
GET /api/v1/player/profile
Authorization: Bearer <access_token>
```

#### Get Balance
```http
GET /api/v1/player/balance
Authorization: Bearer <access_token>
```

#### Get Statistics
```http
GET /api/v1/player/stats
Authorization: Bearer <access_token>
```

### Admin Endpoints

#### Dashboard
```http
GET /api/v1/admin/dashboard
Authorization: Bearer <access_token>
```

#### Update Game Level
```http
PUT /api/v1/admin/levels/{level_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "entry_cost": 150,
  "reward_multiplier": 2.0,
  "time_limit": 90
}
```

#### Ban Player
```http
POST /api/v1/admin/players/{player_id}/ban
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "reason": "Cheating detected"
}
```

## 🔌 WebSocket API

### Connection
```javascript
const ws = new WebSocket(
  'ws://localhost:8000/api/v1/socket/ws?token=<access_token>&device_fingerprint=<hash>&ip_address=<ip>'
);
```

### Message Types

#### Ping/Pong
```json
{
  "type": "ping",
  "timestamp": 1640995200000
}
```

#### Game Action
```json
{
  "type": "game_action",
  "game_id": "game_id",
  "action_data": {
    "type": "click",
    "position": {"x": 100, "y": 200},
    "duration": 150,
    "success": true
  },
  "timestamp": 1640995200000
}
```

#### Game State Update
```json
{
  "type": "game_state_update",
  "game_id": "game_id",
  "state_data": {
    "current_state": {...},
    "progress": 75.5
  },
  "timestamp": 1640995200000
}
```

## 🎮 Game Types

### Color Match
- **Objective**: Sort colored balls into matching tubes
- **Difficulty**: Scales with level (more colors, more tubes)
- **Reward**: Based on completion percentage

### Tube Filling
- **Objective**: Fill tubes with matching liquids
- **Difficulty**: Increases with level complexity
- **Reward**: Partial refunds for effort

## 🔒 Security Features

### Authentication Flow
1. **Wallet Verification**: Ethereum wallet address validation
2. **Device Fingerprinting**: Browser/device signature
3. **IP Validation**: Geographic and security checks
4. **Token Rotation**: Automatic refresh token rotation
5. **Session Management**: Secure session tracking

### Anti-Cheat Measures
1. **Replay Analysis**: Full action sequence recording
2. **Pattern Detection**: Unnatural behavior identification
3. **Speed Monitoring**: Real-time action timing analysis
4. **Device Validation**: Hardware fingerprint verification
5. **IP Tracking**: Geographic and proxy detection

## 📊 Analytics

### Player Analytics
- Game completion rates
- Time-based patterns
- Difficulty progression
- Retry behavior analysis
- Revenue generation

### Platform Analytics
- Total players and games
- Revenue metrics
- Game type distribution
- Player engagement
- Cheat detection rates

### Heatmaps
- Click frequency visualization
- Interaction patterns
- Rage-quit zones
- Success/failure areas

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t gaming-platform .

# Run container
docker run -p 8000:8000 gaming-platform
```

### Production Considerations
1. **Environment Variables**: Secure configuration management
2. **Database**: MongoDB Atlas or self-hosted cluster
3. **Redis**: For session management and caching
4. **Load Balancer**: For horizontal scaling
5. **Monitoring**: Application performance monitoring
6. **Backup**: Regular database backups
7. **SSL/TLS**: HTTPS encryption
8. **Rate Limiting**: API protection

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### API Testing
```bash
# Using curl
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x123...", "username": "test"}'
```

## 📈 Performance

### Benchmarks
- **API Response Time**: < 100ms average
- **WebSocket Latency**: < 50ms
- **Database Queries**: Optimized with indexes
- **Concurrent Users**: 1000+ simultaneous connections

### Optimization
- Async/await throughout
- Database connection pooling
- Redis caching for sessions
- Efficient query patterns
- Background task processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the troubleshooting guide

## 🔮 Roadmap

- [ ] Additional game types
- [ ] Tournament system
- [ ] NFT integration
- [ ] Mobile app support
- [ ] Advanced analytics
- [ ] Multi-language support
- [ ] Social features
- [ ] Blockchain integration

---

**Built with ❤️ for the gaming community** 