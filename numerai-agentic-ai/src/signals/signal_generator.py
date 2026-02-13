import logging
import os

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class NumeraiSignalGenerator:
    """
    Generates signals compliant with Numerai tournament format.
    Phase 1: Simple composite model.
    """

    def __init__(self):
        pass

    def generate_from_analysis(
        self,
        news_sentiment: dict[str, float],
        fundamentals: dict[str, dict],
        sec_insights: dict[str, dict],
    ) -> pd.DataFrame:
        """
        Combine inputs into a composite signal [0, 1]
        """

        signals = []
        timestamp = pd.Timestamp.now()

        all_tickers = set(news_sentiment.keys()) | set(fundamentals.keys())

        for ticker in all_tickers:
            # 1. Sentiment (0-1 normalized, default 0.5)
            sent = news_sentiment.get(ticker, 0.0)
            sent_norm = (sent + 1) / 2  # Assuming -1 to 1 input

            # 2. Fundamentals (PE ratio inverse)
            # This is a mock logic for Phase 1
            fund_data = fundamentals.get(ticker, {}).get("metric", {})
            pe = fund_data.get("peAnnual", 20)
            if pe is None:
                pe = 20
            val_score = 1.0 / (1.0 + np.exp((pe - 20) / 10))  # Sigmoid around PE 20

            # 3. Composite
            # 40% Sentiment, 60% Valuation
            raw_signal = (0.4 * sent_norm) + (0.6 * val_score)

            # Clip to [0, 1] strictly
            final_signal = np.clip(raw_signal, 0.01, 0.99)

            signals.append({"ticker": ticker, "signal": final_signal, "timestamp": timestamp})

        df = pd.DataFrame(signals)
        return df

    def export_for_numerai(self, df: pd.DataFrame, output_path: str = "data/signals/output.csv"):
        """Export to CSV format required by Numerai"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Numerai usually requires 'id', 'prediction'
        # Mapping ticker to id would happen here if we had the mapping file
        # For now exporting ticker/signal for Phase 1 verification
        df.to_csv(output_path, index=False)
        logger.info(f"Signals exported to {output_path}")
