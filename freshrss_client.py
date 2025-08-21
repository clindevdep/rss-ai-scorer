"""
FreshRSS API client for retrieving articles
"""
import requests
import json
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from keyword_scorer import Article
from config import FRESHRSS_API_URL, FRESHRSS_API_TOKEN

class FreshRSSClient:
    """Client for interacting with FreshRSS Google Reader API"""
    
    def __init__(self, username: str, password: str):
        self.base_url = FRESHRSS_API_URL
        self.username = username
        self.password = password
        # Use pre-configured token if available
        self.auth_token = FRESHRSS_API_TOKEN
        self.session = requests.Session()
        
    def authenticate(self) -> bool:
        """Authenticate with FreshRSS Google Reader API"""
        # Skip authentication if we already have a token
        if self.auth_token:
            print(f"✓ Using pre-configured API token: {self.auth_token[:20]}...")
            return True
            
        try:
            # Use proper Google Reader API authentication endpoint
            auth_url = f"{self.base_url}/accounts/ClientLogin"
            
            # Google Reader API authentication
            login_data = {
                'Email': self.username,
                'Passwd': self.password,
                'service': 'reader',
                'accountType': 'HOSTED_OR_GOOGLE',
                'source': 'FreshRSS'
            }
            
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            auth_response = self.session.post(auth_url, data=login_data, headers=headers)
            
            if auth_response.status_code == 200:
                # Parse authentication response
                lines = auth_response.text.strip().split('\n')
                for line in lines:
                    if line.startswith('Auth='):
                        self.auth_token = line.split('=', 1)[1]
                        print(f"✓ Authentication successful, token: {self.auth_token[:20]}...")
                        return True
                print("✗ Auth token not found in response")
                return False
            else:
                print(f"Authentication failed: {auth_response.status_code}")
                print(f"Response: {auth_response.text}")
                return False
                
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def get_articles(
        self, 
        limit: int = 100,
        since_hours: int = 24,
        unread_only: bool = False
    ) -> List[Article]:
        """
        Fetch articles from FreshRSS
        """
        if not self.auth_token and not self.authenticate():
            print("Authentication required")
            return []
        
        try:
            # Use proper Google Reader API stream endpoint
            stream_id = "user/-/state/com.google/reading-list"  # All articles
            if unread_only:
                stream_id = "user/-/state/com.google/reading-list"
            
            # Calculate timestamp for since parameter
            since_timestamp = int((datetime.now() - timedelta(hours=since_hours)).timestamp())
            
            # Prepare request parameters
            params = {
                'output': 'json',
                'n': limit,
                'ot': since_timestamp,  # Older than timestamp (FreshRSS uses this format)
                'ck': int(time.time())  # Cache killer
            }
            
            # Add authorization header
            headers = {
                'Authorization': f'GoogleLogin auth={self.auth_token}'
            }
            
            # Make request to stream/contents endpoint
            stream_url = f"{self.base_url}/stream/contents/{stream_id}"
            response = self.session.get(stream_url, params=params, headers=headers)
            
            if response.status_code != 200:
                print(f"API request failed: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return []
            
            # Parse JSON response
            data = response.json()
            
            if 'items' not in data:
                print(f"No items in response. Keys: {data.keys()}")
                return []
            
            articles = []
            for item in data['items']:
                try:
                    # Extract article data
                    article_id = item.get('id', '')
                    title = item.get('title', 'Untitled')
                    
                    # Get content from summary or content
                    content = ''
                    if 'summary' in item:
                        content = item['summary'].get('content', '')
                    elif 'content' in item:
                        content = item['content'].get('content', '')
                    
                    # Clean HTML from content
                    import re
                    content = re.sub(r'<[^>]+>', '', content)
                    
                    # Get URL and source
                    url = ''
                    if 'canonical' in item:
                        url = item['canonical'][0].get('href', '') if item['canonical'] else ''
                    elif 'alternate' in item:
                        url = item['alternate'][0].get('href', '') if item['alternate'] else ''
                    
                    source = item.get('origin', {}).get('title', 'Unknown')
                    
                    # Get timestamp
                    timestamp = item.get('published', int(time.time()))
                    
                    # Get categories
                    categories = []
                    if 'categories' in item:
                        categories = [cat.split('/')[-1] for cat in item['categories'] if 'label' in cat]
                    
                    article = Article(
                        id=article_id,
                        title=title,
                        content=content,
                        url=url,
                        source=source,
                        timestamp=timestamp,
                        categories=categories
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue
            
            print(f"✓ Retrieved {len(articles)} articles from FreshRSS")
            return articles
            
        except Exception as e:
            print(f"Error fetching articles: {e}")
            return []
    
    def mark_as_read(self, article_ids: List[str]) -> bool:
        """Mark articles as read in FreshRSS"""
        if not self.auth_token:
            return False
            
        try:
            # Use Google Reader API edit-tag endpoint
            edit_url = f"{self.base_url}/edit-tag"
            
            headers = {
                'Authorization': f'GoogleLogin auth={self.auth_token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            for article_id in article_ids:
                data = {
                    'i': article_id,
                    'a': 'user/-/state/com.google/read',  # Add read state
                    'ac': 'edit-tags'
                }
                
                response = self.session.post(edit_url, data=data, headers=headers)
                
                if response.status_code != 200:
                    print(f"Failed to mark article {article_id} as read: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error marking articles as read: {e}")
            return False
