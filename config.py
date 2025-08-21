"""
RSS AI Scorer Configuration
"""
import os
import json
from typing import Dict, Any

# Load environment variables from parent directory .env file
def load_env_from_file():
    """Load environment variables from /home/clindevdep/.env"""
    env_path = "/home/clindevdep/.env"
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")

# Load environment variables
load_env_from_file()

# FreshRSS API Configuration
FRESHRSS_BASE_URL = os.getenv("FRESHRSS_BASE_URL", "http://localhost:8085")
FRESHRSS_API_URL = f"{FRESHRSS_BASE_URL}/api/greader.php"
FRESHRSS_API_TOKEN = os.getenv("FRESHRSS_API_TOKEN")  # Pre-authenticated token

# Dashboard Configuration  
DASHBOARD_BASE_URL = os.getenv("DASHBOARD_BASE_URL", "https://news.clindevdep.com")
DASHBOARD_URL = DASHBOARD_BASE_URL.rstrip('/')  # Remove trailing slash

# API Keys (set via environment variables)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # For Gemini Flash
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # For Claude Sonnet
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # For embeddings

# Scoring Configuration
SCORING_CONFIG = {
    "weights": {
        "keyword_score": 0.3,      # 30% keyword-based scoring
        "semantic_score": 0.4,     # 40% semantic similarity
        "ai_score": 0.3           # 30% AI-powered relevance
    },
    "thresholds": {
        "high_relevance": 75,     # Articles scoring 75+ are high relevance
        "medium_relevance": 50,   # Articles scoring 50-74 are medium
        "low_relevance": 25       # Articles scoring 25-49 are low
    },
    "batch_sizes": {
        "embedding": 50,          # Process 50 articles at once for embeddings
        "ai_scoring": 20          # Process 20 articles at once for AI scoring
    }
}

# Topic Scores Configuration
def load_topic_scores():
    """Load personalized topic scores from JSON file"""
    try:
        import os
        # Look for the file in current directory or parent directory
        file_paths = [
            "topic_scores_100_personalized.json",
            "../topic_scores_100_personalized.json",
            os.path.join(os.path.dirname(__file__), "..", "topic_scores_100_personalized.json")
        ]
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return {
                        topic["topic"]: topic["score"] 
                        for topic in data["complete_topic_list"]
                    }
    except Exception as e:
        print(f"Error loading topic scores: {e}")
        return {}

TOPIC_SCORES = load_topic_scores()

# Keywords for each high-scoring topic
HIGH_VALUE_KEYWORDS = {
    "Problem Solving & Critical Thinking": {
        "positive": ["critical thinking", "problem solving", "analytical", "logic", "reasoning", "methodology", "analysis", "systematic"],
        "negative": ["opinion", "speculation", "rumor"]
    },
    "Artificial Intelligence": {
        "positive": ["artificial intelligence", "AI", "machine learning", "ML", "deep learning", "neural networks", "GPT", "LLM", "transformers"],
        "negative": ["AI hype", "AI bubble", "overhyped"]
    },
    "Machine Learning": {
        "positive": ["machine learning", "ML", "algorithms", "models", "training", "inference", "datasets", "supervised", "unsupervised"],
        "negative": ["basic tutorial", "beginner guide"]
    },
    "Investigative Journalism": {
        "positive": ["investigation", "investigative", "expose", "revealed", "uncovered", "leaked", "documents", "whistleblower", "exclusive"],
        "negative": ["gossip", "rumor", "unverified"]
    },
    "Technology Innovation": {
        "positive": ["innovation", "breakthrough", "revolutionary", "cutting-edge", "novel", "advancement", "pioneering"],
        "negative": ["incremental", "minor update", "cosmetic"]
    },
    "Computer Science": {
        "positive": ["computer science", "algorithms", "data structures", "computational", "programming", "software engineering", "systems"],
        "negative": ["basic programming", "hello world"]
    },
    "European Politics": {
        "positive": ["european union", "EU", "european parliament", "brussels", "european politics", "eurozone", "schengen"],
        "negative": ["celebrity politics", "gossip"]
    },
    "Cybersecurity": {
        "positive": ["cybersecurity", "security", "vulnerability", "exploit", "breach", "malware", "encryption", "privacy", "zero-day"],
        "negative": ["security theater", "fear mongering"]
    }
}

# Source reliability weights
SOURCE_WEIGHTS = {
    "high_reliability": 1.5,  # Nature, Science, Bellingcat, Reuters
    "medium_reliability": 1.0,  # Most mainstream sources
    "low_reliability": 0.8     # Questionable sources
}

# Regional preferences
REGIONAL_WEIGHTS = {
    "czech": 1.5,     # 1.5x for Czech content
    "european": 1.3,  # 1.3x for European content
    "global": 1.0     # 1.0x for global content
}

# Freshness decay configuration
FRESHNESS_CONFIG = {
    "max_age_hours": 168,     # 1 week maximum
    "half_life_hours": 24,    # Score halves every 24 hours
    "min_multiplier": 0.1     # Minimum freshness multiplier
}
