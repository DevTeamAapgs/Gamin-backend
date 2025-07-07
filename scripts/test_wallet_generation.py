#!/usr/bin/env python3
"""
Test script for unique wallet address generation
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.utils.helpers import generate_unique_wallet_address

def test_wallet_address_generation():
    """Test the wallet address generation functionality"""
    
    print("Testing Unique Wallet Address Generation")
    print("=" * 50)
    
    # Generate multiple wallet addresses to ensure uniqueness
    addresses = []
    for i in range(5):
        address = generate_unique_wallet_address()
        addresses.append(address)
        print(f"Generated address {i+1}: {address}")
    
    # Check for uniqueness
    unique_addresses = set(addresses)
    if len(unique_addresses) == len(addresses):
        print(f"\n✓ All {len(addresses)} addresses are unique!")
    else:
        print(f"\n✗ Found duplicate addresses!")
        print(f"Generated: {len(addresses)}, Unique: {len(unique_addresses)}")
    
    # Check format
    print("\nChecking address format:")
    for i, address in enumerate(addresses):
        if address.startswith("0x") and len(address) == 42:
            print(f"✓ Address {i+1}: Valid format")
        else:
            print(f"✗ Address {i+1}: Invalid format (length: {len(address)})")
    
    # Check hex characters
    print("\nChecking hex characters:")
    for i, address in enumerate(addresses):
        hex_part = address[2:]  # Remove "0x" prefix
        if all(c in '0123456789abcdef' for c in hex_part):
            print(f"✓ Address {i+1}: Valid hex characters")
        else:
            print(f"✗ Address {i+1}: Invalid hex characters")

def test_wallet_address_examples():
    """Show examples of generated wallet addresses"""
    
    print("\n" + "=" * 50)
    print("Example Wallet Addresses")
    print("=" * 50)
    
    for i in range(10):
        address = generate_unique_wallet_address()
        print(f"Example {i+1:2d}: {address}")

if __name__ == "__main__":
    test_wallet_address_generation()
    test_wallet_address_examples()
    print("\n✓ Wallet address generation tests completed!") 