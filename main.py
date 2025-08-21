#!/usr/bin/env python3
"""
RSS AI Scorer - Main application entry point and CLI
"""
import argparse
import json
import os
from datetime import datetime
from typing import Optional

from simple_scorer import SimpleScorer
from freshrss_client import FreshRSSClient
from keyword_scorer import Article
from newsletter_generator import NewsletterGenerator

def print_banner():
    """Print application banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                     RSS AI Scorer v1.0                      ║
    ║              AI-Powered RSS Article Scoring System           ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def setup_environment(interactive=True):
    """Setup environment and check API keys"""
    missing_keys = []
    
    # Check API keys
    if not os.getenv("GOOGLE_API_KEY"):
        missing_keys.append("GOOGLE_API_KEY (for Gemini Flash)")
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing_keys.append("ANTHROPIC_API_KEY (for Claude Sonnet)")
    
    if not os.getenv("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY (for embeddings)")
    
    if missing_keys:
        print("⚠️  Missing API keys:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nSet these environment variables to enable full functionality.")
        print("The system will work with limited features without some keys.")
        if interactive:
            input("\nPress Enter to continue or Ctrl+C to exit...")
        else:
            print("⚠️  Running in non-interactive mode, continuing with limited features...")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="RSS AI Scorer - AI-Powered Article Scoring")
    parser.add_argument("--username", "-u", help="FreshRSS username")
    parser.add_argument("--password", "-p", help="FreshRSS password")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Number of articles to process (default: 10)")
    parser.add_argument("--api", action="store_true", help="Start API server mode")
    parser.add_argument("--simple", action="store_true", help="Use simple AI scoring (recommended)")
    parser.add_argument("--newsletter", action="store_true", help="Generate and send newsletter")
    parser.add_argument("--since-hours", type=int, help="Only process articles from last N hours")
    parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if not args.non_interactive:
        print_banner()
        setup_environment(interactive=True)
    else:
        setup_environment(interactive=False)
    
    if args.api:
        # Start API server
        import uvicorn
        from web_app import app
        
        print("🚀 Starting RSS AI Scorer API server...")
        print("📊 Dashboard available at: http://localhost:8000")
        print("📖 API docs at: http://localhost:8000/docs")
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
        return
    
    # Validate required arguments
    if not args.username or not args.password:
        if not args.non_interactive:
            print("❌ Username and password are required")
            print("Use --username and --password or --api for server mode")
            return
        else:
            # In non-interactive mode, try to get credentials from environment
            args.username = os.getenv("FRESHRSS_USERNAME")
            args.password = os.getenv("FRESHRSS_API_PASSWORD")
            
            if not args.username or not args.password:
                print("❌ FreshRSS credentials not configured")
                return
    
    # Process articles
    try:
        if args.simple:
            scorer = SimpleScorer()
        else:
            print("⚠️  Defaulting to simple scoring (recommended)")
            scorer = SimpleScorer()
        
        client = FreshRSSClient(args.username, args.password)
        
        if not client.authenticate():
            print("❌ Failed to authenticate with FreshRSS")
            return
        
        print(f"📚 Getting articles (limit: {args.limit})...")
        articles = client.get_articles(
            limit=args.limit,
            since_hours=args.since_hours,
            unread_only=False
        )
        
        if not articles:
            print("📭 No articles found")
            return
        
        print(f"📊 Processing {len(articles)} articles...")
        
        scored_articles = []
        for i, article in enumerate(articles, 1):
            if args.verbose:
                print(f"\n[{i}/{len(articles)}] Processing: {article.title[:60]}...")
            
            try:
                scored_result = scorer.score_article(article)
                scored_articles.append({
                    "article": article,
                    "result": scored_result
                })
                
                if args.verbose:
                    print(f"   Score: {scored_result.assigned_score}")
                    print(f"   Topic: {scored_result.primary_topic}")
                    if scored_result.ai_reasoning:
                        print(f"   Reasoning: {scored_result.ai_reasoning[:100]}...")
                
            except Exception as e:
                print(f"❌ Error scoring article: {e}")
                continue
        
        # Sort by score
        scored_articles.sort(key=lambda x: x["result"].assigned_score, reverse=True)
        
        if not args.non_interactive:
            print(f"\n📊 Scoring Results ({len(scored_articles)} articles):")
            print("=" * 80)
            
            for item in scored_articles[:20]:  # Show top 20
                article = item["article"]
                result = item["result"]
                print(f"[{result.assigned_score:3.0f}] {result.primary_topic:<20} {article.title[:50]}")
        
        # Generate newsletter if requested
        if args.newsletter:
            print("\n📧 Generating newsletter...")
            
            # Create newsletter data
            newsletter_articles = []
            for item in scored_articles:
                article = item["article"]
                result = item["result"]
                
                newsletter_articles.append({
                    "id": article.id,
                    "title": article.title,
                    "summary": result.ai_reasoning or article.content[:200] + "...",
                    "url": article.url,
                    "source": article.source,
                    "score": result.assigned_score,
                    "tags": [result.primary_topic] if result.primary_topic else []
                })
            
            # Send newsletter
            from email_notifications import EmailNotificationSystem
            email_system = EmailNotificationSystem()
            
            success = email_system.send_newsletter(
                articles=newsletter_articles[:15],  # Top 15 articles
                subject=f"📰 RSS AI Newsletter - {datetime.now().strftime('%B %d, %Y')}"
            )
            
            if success:
                print("✅ Newsletter sent successfully!")
            else:
                print("❌ Newsletter sending failed")
        
        print(f"\n✅ Processing complete. {len(scored_articles)} articles scored.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
