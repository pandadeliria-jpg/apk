#!/usr/bin/env python3
"""
Roblox Android Account Creator
Uses mobile API to bypass captcha (Android app doesn't show captcha on signup)
"""
import sys
import os
import random
import string
import json
import urllib.request
import urllib.parse
import urllib.error
import time

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from roblox_jni import RobloxNetworking, RobloxCrypto


def generate_username(length=12):
    """Generate random username."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_password(length=16):
    """Generate random password."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))


def generate_birthdate():
    """Generate random birthdate (18-25 years old)."""
    year = random.randint(1995, 2005)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


class RobloxAccountCreator:
    """
    Create Roblox accounts using Android mobile API.
    The mobile API doesn't require captcha for signup!
    """
    
    def __init__(self):
        self.network = RobloxNetworking()
        self.created_accounts = []
    
    def check_username(self, username: str) -> bool:
        """Check if username is available."""
        return self.network.check_username(username)
    
    def create_account(self, username: str = None, password: str = None, 
                       birthdate: str = None, gender: str = "Male",
                       max_retries: int = 5) -> dict:
        """
        Create a new Roblox account.
        
        Returns:
            dict with success status, userId, username, password, cookie
        """
        # Generate credentials if not provided
        if not username:
            username = generate_username()
        if not password:
            password = generate_password()
        if not birthdate:
            birthdate = generate_birthdate()
        
        print(f"[*] Creating account...")
        print(f"    Username: {username}")
        print(f"    Birthdate: {birthdate}")
        
        # Check username availability first
        for attempt in range(max_retries):
            if attempt > 0:
                username = generate_username()
                print(f"[!] Username taken, trying: {username}")
            
            if self.check_username(username):
                break
        else:
            print("[!] Could not find available username")
            return {'success': False, 'error': 'No available username'}
        
        # Attempt signup
        result = self.network.signup(username, password, birthdate, gender)
        
        if result and result.get('userId'):
            account = {
                'success': True,
                'userId': result['userId'],
                'username': username,
                'password': password,
                'cookie': result.get('cookie', ''),
                'birthdate': birthdate,
            }
            self.created_accounts.append(account)
            print(f"[+] Account created!")
            print(f"    User ID: {account['userId']}")
            print(f"    Username: {username}")
            print(f"    Password: {password}")
            return account
        else:
            print("[!] Signup failed")
            return {'success': False, 'error': 'Signup request failed'}
    
    def create_multiple(self, count: int, save_file: str = None) -> List[dict]:
        """Create multiple accounts."""
        accounts = []
        
        for i in range(count):
            print(f"\n{'='*40}")
            print(f"[*] Account {i+1}/{count}")
            print(f"{'='*40}")
            
            account = self.create_account()
            if account['success']:
                accounts.append(account)
            
            # Delay between accounts
            if i < count - 1:
                delay = random.uniform(2, 5)
                print(f"[*] Waiting {delay:.1f}s before next account...")
                time.sleep(delay)
        
        # Save to file
        if save_file and accounts:
            self.save_accounts(accounts, save_file)
        
        return accounts
    
    def save_accounts(self, accounts: List[dict], filename: str):
        """Save accounts to file."""
        with open(filename, 'a') as f:
            for acc in accounts:
                f.write(f"{acc['username']}:{acc['password']}:{acc['userId']}\n")
        print(f"\n[+] Saved {len(accounts)} accounts to {filename}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Roblox Android Account Creator")
    parser.add_argument("--count", type=int, default=1, help="Number of accounts to create")
    parser.add_argument("--output", type=str, default="roblox_accounts.txt", help="Output file")
    parser.add_argument("--username", type=str, help="Specific username (optional)")
    parser.add_argument("--password", type=str, help="Specific password (optional)")
    args = parser.parse_args()
    
    print("="*60)
    print("Roblox Android Account Creator")
    print("Uses mobile API to bypass captcha!")
    print("="*60)
    print()
    
    creator = RobloxAccountCreator()
    
    if args.count == 1 and (args.username or args.password):
        # Single account with specific credentials
        account = creator.create_account(
            username=args.username,
            password=args.password
        )
        if account['success']:
            creator.save_accounts([account], args.output)
    else:
        # Multiple accounts
        accounts = creator.create_multiple(args.count, args.output)
    
    print("\n" + "="*60)
    print(f"Total accounts created: {len(creator.created_accounts)}")
    print("="*60)


if __name__ == "__main__":
    main()
