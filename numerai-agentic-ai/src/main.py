import argparse
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Import modules
from data.perplexity_devkit import PerplexityNumeraiDevKit
from data.finnhub_fetcher import FinnhubDataFetcher
from agents.numerai_crew import NumeraiAgentCrew
from signals.signal_generator import NumeraiSignalGenerator

# Load env
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Numerai Agentic AI - Phase 1 Pipeline")
    parser.add_argument("--mode", type=str, default="production", help="Execution mode")
    parser.add_argument("--tickers", type=str, default="AAPL,MSFT,GOOGL,AMZN,NVDA", help="Comma-sep tickers")
    args = parser.parse_args()
    
    logger.info(f"Starting Numerai Agentic AI in {args.mode} mode")
    
    # 1. Init Components
    perp_key = os.getenv("PERPLEXITY_API_KEY")
    finnhub_key = os.getenv("FINNHUB_API_KEY")
    
    if not perp_key or not finnhub_key:
        logger.error("Missing API keys. Check .env file.")
        return

    perplexity = PerplexityNumeraiDevKit(perp_key)
    finnhub_client = FinnhubDataFetcher(finnhub_key)
    crew = NumeraiAgentCrew(perplexity, finnhub_client)
    generator = NumeraiSignalGenerator()
    
    tickers = args.tickers.split(",")
    
    # 2. Data Fetching (Agentic)
    logger.info("Step 1: Fetching Market News (Agentic)...")
    news_data = perplexity.batch_market_news([f"{t} market analysis" for t in tickers])
    
    logger.info("Step 2: Fetching Fundamentals...")
    fund_data = finnhub_client.batch_fetch_fundamentals(tickers)
    
    # 3. Agentic Analysis (CrewAI)
    # Note: In production, the crew would consume news_data/fund_data. 
    # For now, we trigger the orchestration demo.
    logger.info("Step 3: Running Agent Crew...")
    # crew_output = crew.generate_signals(tickers) # Uncomment to run full crew (eats tokens)
    
    # 4. Signal Generation (Mocking sentiment from news for now)
    logger.info("Step 4: Generating Signals...")
    
    # Simple sentiment extraction mock from news
    sentiment_map = {}
    for query, items in news_data.items():
        # Simplistic sentiment averager
        ticker = query.split()[0]
        avg_sent = 0.5
        if items and isinstance(items, list):
            valid_sents = [i.get('sentiment', 0) for i in items if 'sentiment' in i]
            if valid_sents:
                avg_sent = sum(valid_sents) / len(valid_sents)
        sentiment_map[ticker] = avg_sent
        
    signals_df = generator.generate_from_analysis(sentiment_map, fund_data, {})
    
    # 5. Export
    generator.export_for_numerai(signals_df, "numerai-agentic-ai/data/output.csv")
    
    # 6. Monitoring Report (Phase 2)
    health = perplexity.get_health_metrics()
    logger.info(f"Pipeline Complete. Health: {health}")

if __name__ == "__main__":
    main()
