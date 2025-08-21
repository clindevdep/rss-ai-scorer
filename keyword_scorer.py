"""
Keyword-based scoring component for RSS articles
"""
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from config import HIGH_VALUE_KEYWORDS, TOPIC_SCORES

@dataclass
class Article:
    """Article data structure"""
    id: str
    title: str
    content: str
    url: str
    source: str
    timestamp: int
    categories: List[str] = None

class KeywordScorer:
    """Keyword-based scoring system"""
    
    def __init__(self):
        self.topic_scores = TOPIC_SCORES
        self.keywords = HIGH_VALUE_KEYWORDS
        
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def calculate_keyword_matches(self, article: Article) -> Dict[str, float]:
        """Calculate keyword matches for each topic"""
        full_text = f"{article.title} {article.content}".lower()
        topic_matches = {}
        
        for topic, keywords in self.keywords.items():
            positive_matches = 0
            negative_matches = 0
            
            # Count positive keyword matches
            for keyword in keywords.get("positive", []):
                if keyword.lower() in full_text:
                    # Weight longer phrases more heavily
                    weight = len(keyword.split())
                    positive_matches += weight
            
            # Count negative keyword matches
            for keyword in keywords.get("negative", []):
                if keyword.lower() in full_text:
                    weight = len(keyword.split())
                    negative_matches += weight
            
            # Calculate net match score
            net_matches = positive_matches - (negative_matches * 0.5)
            topic_matches[topic] = max(0, net_matches)
        
        return topic_matches
    
    def score_article(self, article: Article) -> Tuple[float, Dict[str, any]]:
        """
        Score article based on keyword matching
        Returns: (score, details)
        """
        keyword_matches = self.calculate_keyword_matches(article)
        
        # Calculate weighted score based on topic preferences
        total_score = 0
        total_weight = 0
        
        for topic, match_count in keyword_matches.items():
            if match_count > 0:
                topic_score = self.topic_scores.get(topic, 50)  # Default to 50 if topic not found
                weighted_contribution = topic_score * match_count
                total_score += weighted_contribution
                total_weight += match_count
        
        # Normalize score to 0-100 range
        if total_weight > 0:
            keyword_score = min(100, (total_score / total_weight))
        else:
            keyword_score = 30  # Default score for articles with no keyword matches
        
        details = {
            "keyword_matches": keyword_matches,
            "total_matches": sum(keyword_matches.values()),
            "contributing_topics": [topic for topic, count in keyword_matches.items() if count > 0]
        }
        
        return keyword_score, details

    def score_articles_batch(self, articles: List[Article]) -> List[Dict[str, any]]:
        """
        Score multiple articles efficiently
        """
        results = []
        
        for article in articles:
            score, details = self.score_article(article)
            
            result = {
                "article": article,
                "keyword_score": score,
                "details": details,
                "scoring_method": "keyword"
            }
            
            results.append(result)
        
        return results
