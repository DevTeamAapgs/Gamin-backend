# 🎮 Gaming Platform Backend

A production-grade play-to-earn crypto gaming platform built with FastAPI, featuring real-time gameplay, secure authentication, comprehensive analytics, and advanced security measures.

## 📚 Documentation Hub

This README serves as your central navigation hub. Click on any section below to explore detailed documentation:

### 🏗️ [Project Architecture & Overview](PROJECT_SUMMARY.md)
- Complete system architecture overview
- Database design and collections structure
- API endpoints comprehensive list
- Performance metrics and benchmarks
- Deployment strategies

### 🔐 [Security & Authentication](COOKIE_AUTH_IMPLEMENTATION.md)
- Triple-layer authentication system (JWT + AES + Device fingerprinting)
- Cookie-based authentication implementation
- Anti-cheat measures and security features
- Token management and session handling

### 🛡️ [Encryption & Crypto Utilities](CRYPTO_USAGE_GUIDE.md)
- AES-256-CBC encryption with PBKDF2 key derivation
- Request/response encryption middleware
- Selective field encryption for sensitive data
- Domain-specific encryption (game, payment, user data)

### 📊 [Logging & Monitoring](LOGGING_IMPLEMENTATION.md)
- Comprehensive database logging system
- HTTP request logs with full context
- Security event monitoring and alerts
- Game action tracking for anti-cheat
- Real-time analytics and heatmap generation

### 👥 [User Management System](USER_MANAGEMENT_API_SUMMARY.md)
- Complete user CRUD operations
- Role-based access control
- Player profile management
- Wallet address generation
- Status management and soft deletes

### 🎭 [Roles & Permissions](ROLES_IMPLEMENTATION.md)
- Hierarchical role management system
- Permission-based access control
- Menu structure and grid-based data display
- Form dependency management
- Bulk operations and status updates

### 🔢 [Prefix Generation System](PREFIX_GENERATION_GUIDE.md)
- Unique identifier generation for all modules
- Sequential numbering with custom prefixes
- Database integration and atomic updates
- Error handling and testing utilities

### 🎯 [Player Role Updates](PLAYER_ROLE_UPDATE_GUIDE.md)
- Role name-based user creation
- Backward compatibility considerations
- Migration strategies and best practices
- Error handling and validation

### 🗄️ [Database Standards](STANDARDIZED_COLLECTIONS.md)
- Standardized collection structure across all modules
- Audit trail implementation (created_by, updated_by, timestamps)
- Soft delete functionality
- Status management with enums
- Database utilities and helper functions

### 📖 [API Documentation](SWAGGER_COOKIE_GUIDE.md)
- Swagger UI configuration with cookie authentication
- Interactive API testing and documentation
- Dual authentication support (cookies + bearer tokens)
- Testing workflows and troubleshooting

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB 4.4+
- Redis (optional)
- Docker (optional)

### Installation

1. **Clone and Setup**
```bash
git clone <repository-url>
cd gaming-platform-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
cp env.example .env
# Edit .env with your configuration
```

3. **Database Setup**
```bash
# Initialize database with roles and collections
python scripts/init_db.py
python scripts/init_roles.py
```

4. **Start the Application**
```bash
python start.py
# Or for development
python -m uvicorn app.main:app --reload
```

5. **Access API Documentation**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🎮 Core Features

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
- **Authentication**: JWT + AES encryption + Cookie-based auth
- **Real-time**: WebSockets
- **Background Tasks**: Celery
- **API Documentation**: Swagger UI / ReDoc
- **Security**: Triple-layer encryption, device fingerprinting
- **Monitoring**: Comprehensive logging and analytics

## 📁 Project Structure

```
backend/
├── app/
│   ├── auth/                 # Authentication & security
│   ├── common/              # Shared utilities
│   ├── core/                # Configuration & enums
│   ├── db/                  # Database connection
│   ├── middleware/          # Request/response middleware
│   ├── models/              # Database models
│   ├── routes/              # API endpoints
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── utils/               # Utility functions
├── scripts/                 # Database initialization
├── public/                  # Static files & uploads
├── templates/               # HTML templates
└── docs/                    # Documentation files
```

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

# Cookie Configuration
COOKIE_DOMAIN=localhost
COOKIE_SECURE=False
COOKIE_HTTPONLY=True
COOKIE_SAMESITE=lax

# Game Configuration
DEFAULT_GAME_TIMER=60
DEFAULT_ENTRY_COST=100
DEFAULT_REWARD_MULTIPLIER=1.5

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin-secure-password
```

## 🚀 Deployment

### Docker Deployment
```bash
# Using docker-compose
docker-compose up -d

# Or using Docker directly
docker build -t gaming-platform .
docker run -p 8000:8000 gaming-platform
```

### Production Considerations
- Environment variable management
- Database clustering (MongoDB Atlas)
- Redis for session management
- Load balancer configuration
- SSL/TLS encryption
- Rate limiting
- Monitoring and logging
- Backup strategies

## 📈 Performance Metrics

### Benchmarks
- **API Response Time**: < 100ms average
- **WebSocket Latency**: < 50ms
- **Database Queries**: Optimized with indexes
- **Concurrent Users**: 1000+ simultaneous connections

### Optimization Techniques
- Async/await throughout the application
- Database connection pooling
- Redis caching for frequently accessed data
- Optimized MongoDB queries with proper indexing
- Background task processing with Celery

## 🔍 Testing

### API Testing
- Swagger UI with cookie authentication
- Comprehensive endpoint testing
- Security validation
- Performance testing

### Database Testing
```bash
# Test prefix generation
python scripts/test_prefix_generation.py

# Test player creation
python scripts/test_player_creation.py

# Test wallet generation
python scripts/test_wallet_generation.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the detailed documentation links above
- Review the troubleshooting sections in each guide
- Open an issue for bugs or feature requests

---

**🎮 Ready to build the future of gaming? Start with the [Project Architecture](PROJECT_SUMMARY.md) to understand the full system, then dive into specific features using the documentation links above!** 