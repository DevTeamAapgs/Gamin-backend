# 🔐 Crypto Utils & Encryption Middleware Usage Guide

## Overview

This guide explains how to use the enhanced crypto utilities and encryption middleware in your gaming platform. The system provides multiple layers of encryption for different use cases.

## 📦 Components

### 1. Enhanced Crypto Utils (`app/utils/enhanced_crypto.py`)
- **AES-256-CBC encryption** with PBKDF2 key derivation
- **Object encryption/decryption** for Python dictionaries
- **Secure token generation** for various purposes
- **Data hashing** for secure storage

### 2. Enhanced Crypto Dependencies (`app/utils/enhanced_crypto_dependencies.py`)
- **Request body decryption** with error handling
- **Selective field decryption** for specific data types
- **Query parameter decryption** with validation
- **Domain-specific decryption** (game, payment, user data)

### 3. Enhanced Encryption Middleware (`app/middleware/enhanced_encryption_middleware.py`)
- **Selective field encryption** in responses
- **Automatic sensitive data detection**
- **Domain-specific response encryption**
- **Full response encryption** when needed

## 🚀 Basic Usage

### 1. Simple Encryption/Decryption

```python
from app.utils.enhanced_crypto import enhanced_crypto

# Encrypt a string
sensitive_data = "player_score_1500"
encrypted = enhanced_crypto.encrypt_aes256(sensitive_data)
decrypted = enhanced_crypto.decrypt_aes256(encrypted)

print(f"Original: {sensitive_data}")
print(f"Encrypted: {encrypted}")
print(f"Decrypted: {decrypted}")
```

### 2. Object Encryption

```python
# Encrypt a Python dictionary
game_data = {
    "player_id": "12345",
    "score": 1500,
    "level": 5,
    "secret_key": "abc123"
}

encrypted_object = enhanced_crypto.encrypt_object(game_data)
decrypted_object = enhanced_crypto.decrypt_object(encrypted_object)

print(f"Original: {game_data}")
print(f"Encrypted: {encrypted_object}")
print(f"Decrypted: {decrypted_object}")
```

## 🔧 Request Encryption

### 1. Encrypted Request Body

```python
from fastapi import APIRouter, Depends
from app.utils.enhanced_crypto_dependencies import decrypt_request_body

router = APIRouter()

@router.post("/secure-endpoint")
async def handle_encrypted_request(decrypted_body: dict = Depends(decrypt_request_body)):
    """Handle encrypted request body."""
    return {
        "message": "Data received and decrypted",
        "data": decrypted_body
    }
```

**Client-side (JavaScript):**
```javascript
// Encrypt data before sending
const sensitiveData = {
    score: "1500",
    level: "5",
    secret_key: "abc123"
};

// Encrypt each field
const encryptedData = {
    score: encryptAES256(sensitiveData.score),
    level: encryptAES256(sensitiveData.level),
    secret_key: encryptAES256(sensitiveData.secret_key)
};

// Send encrypted data
fetch('/api/v1/secure-endpoint', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(encryptedData)
});
```

### 2. Selective Field Decryption

```python
from app.utils.enhanced_crypto_dependencies import decrypt_game_data

@router.post("/game-submission")
async def submit_game(decrypted_data: dict = Depends(decrypt_game_data)):
    """Decrypt only game-specific fields."""
    score = decrypted_data.get("score")
    moves = decrypted_data.get("moves", [])
    
    return {
        "message": "Game data processed",
        "score": score,
        "moves_count": len(moves)
    }
```

### 3. Encrypted Query Parameters

```python
from app.utils.enhanced_crypto_dependencies import decrypt_query_param

@router.get("/secure-query")
async def handle_encrypted_query(encrypted_param: str = Depends(decrypt_query_param)):
    """Handle encrypted query parameter."""
    return {"decrypted_value": encrypted_param}
```

### 4. Domain-Specific Decryption

```python
from app.utils.enhanced_crypto_dependencies import (
    decrypt_payment_data,
    decrypt_user_data,
    decrypt_score,
    decrypt_wallet_address
)

@router.post("/payment")
async def process_payment(payment_data: dict = Depends(decrypt_payment_data)):
    """Handle encrypted payment data."""
    return {"status": "Payment processed"}

@router.get("/user-profile")
async def get_user_profile(wallet: str = Depends(decrypt_wallet_address)):
    """Handle encrypted wallet address."""
    return {"wallet": wallet}
```

## 📤 Response Encryption

### 1. Selective Field Encryption

```python
from app.middleware.enhanced_encryption_middleware import encrypt_sensitive_response

@router.get("/user-data")
async def get_user_data():
    """Return user data with encrypted sensitive fields."""
    user_data = {
        "user_id": "12345",
        "username": "player123",
        "password": "secret_password",
        "wallet_address": "0x1234567890abcdef...",
        "email": "player@example.com"
    }
    
    return encrypt_sensitive_response(user_data)
```

### 2. Domain-Specific Response Encryption

```python
from app.middleware.enhanced_encryption_middleware import (
    encrypt_game_response,
    encrypt_payment_response,
    encrypt_user_response
)

@router.get("/game-data")
async def get_game_data():
    """Return game data with encrypted game-specific fields."""
    game_data = {
        "game_id": "game_123",
        "score": 1500,
        "moves": ["up", "down", "left"],
        "secret_key": "game_secret_789"
    }
    
    return encrypt_game_response(game_data)

@router.get("/payment-info")
async def get_payment_info():
    """Return payment data with encrypted payment fields."""
    payment_data = {
        "transaction_id": "txn_123",
        "amount": 100.50,
        "wallet_address": "0xabcdef1234567890...",
        "payment_method": "crypto"
    }
    
    return encrypt_payment_response(payment_data)
```

### 3. Full Response Encryption

```python
from app.middleware.enhanced_encryption_middleware import encrypt_entire_response

@router.get("/super-secret")
async def get_super_secret_data():
    """Return entirely encrypted response."""
    secret_data = {
        "message": "This is super secret",
        "data": "very_sensitive_information"
    }
    
    return encrypt_entire_response(secret_data)
```

## 🎮 Gaming Platform Specific Usage

### 1. Game Score Submission

```python
@router.post("/submit-score")
async def submit_game_score(
    score: Union[int, float] = Depends(decrypt_score),
    current_user: dict = Depends(get_current_user)
):
    """Submit encrypted game score."""
    # Process score
    processed_score = {
        "player_id": current_user.get("sub"),
        "score": score,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return encrypt_game_response(processed_score)
```

### 2. Payment Processing

```python
@router.post("/process-payment")
async def process_crypto_payment(
    payment_data: dict = Depends(decrypt_payment_data),
    current_user: dict = Depends(get_current_user)
):
    """Process encrypted payment data."""
    amount = payment_data.get("amount")
    wallet = payment_data.get("wallet_address")
    
    # Process payment logic here
    
    result = {
        "transaction_id": f"txn_{enhanced_crypto.generate_secure_token(16)}",
        "amount": amount,
        "wallet_address": wallet,
        "status": "completed"
    }
    
    return encrypt_payment_response(result)
```

### 3. User Profile Management

```python
@router.put("/update-profile")
async def update_user_profile(
    user_data: dict = Depends(decrypt_user_data),
    current_user: dict = Depends(get_current_user)
):
    """Update user profile with encrypted data."""
    # Update profile logic here
    
    updated_profile = {
        "user_id": current_user.get("sub"),
        "email": user_data.get("email"),
        "phone": user_data.get("phone"),
        "preferences": user_data.get("preferences")
    }
    
    return encrypt_user_response(updated_profile)
```

## 🔒 Security Best Practices

### 1. Key Management

```python
# Use environment variables for keys
AES_SECRET_KEY = os.getenv("AES_SECRET_KEY", "your-32-byte-key")
CRYPTO_SALT = os.getenv("CRYPTO_SALT", "your-salt-value")

# Never hardcode keys in production
```

### 2. Error Handling

```python
try:
    decrypted_data = enhanced_crypto.decrypt_aes256(encrypted_data)
except ValueError as e:
    logger.error(f"Decryption failed: {e}")
    raise HTTPException(status_code=400, detail="Invalid encrypted data")
```

### 3. Data Validation

```python
def validate_wallet_address(address: str) -> bool:
    """Validate wallet address format."""
    return address.startswith("0x") and len(address) == 42

def validate_score(score: Union[int, float]) -> bool:
    """Validate game score."""
    return isinstance(score, (int, float)) and 0 <= score <= 10000
```

### 4. Logging and Monitoring

```python
import logging

logger = logging.getLogger(__name__)

# Log encryption/decryption operations (without sensitive data)
logger.info("Processing encrypted game submission")
logger.error(f"Decryption failed for user {user_id}")
```

## 🧪 Testing

### 1. Unit Tests

```python
import pytest
from app.utils.enhanced_crypto import enhanced_crypto

def test_basic_encryption():
    original = "test_data"
    encrypted = enhanced_crypto.encrypt_aes256(original)
    decrypted = enhanced_crypto.decrypt_aes256(encrypted)
    assert original == decrypted

def test_object_encryption():
    original = {"key": "value", "number": 123}
    encrypted = enhanced_crypto.encrypt_object(original)
    decrypted = enhanced_crypto.decrypt_object(encrypted)
    assert original == decrypted
```

### 2. Integration Tests

```python
from fastapi.testclient import TestClient

def test_encrypted_endpoint(client: TestClient):
    # Encrypt test data
    test_data = {"score": "1500"}
    encrypted_data = {
        "score": enhanced_crypto.encrypt_aes256("1500")
    }
    
    response = client.post("/api/v1/encrypted/request-body", json=encrypted_data)
    assert response.status_code == 200
    assert response.json()["decrypted_data"]["score"] == "1500"
```

## 📋 Configuration

### Environment Variables

```env
# Crypto Configuration
AES_SECRET_KEY=your-32-byte-aes-key-for-encryption
CRYPTO_SALT=your-salt-for-encryption
AES_KEY=your-32-byte-aes-key-for-encryption
SALT=your-salt-for-encryption
```

### Dependencies

```txt
pycryptodome==3.23.0
cryptography==42.0.7
```

## 🚨 Important Notes

1. **Key Security**: Never commit encryption keys to version control
2. **Performance**: Encryption/decryption adds overhead - use selectively
3. **Compatibility**: Ensure client-side encryption matches server-side
4. **Error Handling**: Always handle encryption/decryption errors gracefully
5. **Logging**: Log encryption operations but never log sensitive data
6. **Testing**: Test encryption/decryption thoroughly in your test suite

## 🔄 Migration from Basic Crypto

If you're migrating from the basic crypto utils:

1. **Replace imports**:
   ```python
   # Old
   from app.utils.crypto import encrypt_aes256, decrypt_aes256
   
   # New
   from app.utils.enhanced_crypto import enhanced_crypto
   ```

2. **Update function calls**:
   ```python
   # Old
   encrypted = encrypt_aes256(data)
   decrypted = decrypt_aes256(encrypted)
   
   # New
   encrypted = enhanced_crypto.encrypt_aes256(data)
   decrypted = enhanced_crypto.decrypt_aes256(encrypted)
   ```

3. **Use enhanced features**:
   ```python
   # Object encryption
   encrypted_obj = enhanced_crypto.encrypt_object(my_dict)
   decrypted_obj = enhanced_crypto.decrypt_object(encrypted_obj)
   
   # Secure token generation
   token = enhanced_crypto.generate_secure_token(32)
   ```

This enhanced crypto system provides enterprise-grade security for your gaming platform while maintaining ease of use and flexibility. 