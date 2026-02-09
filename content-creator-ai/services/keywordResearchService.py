import os
from typing import Dict, List, Optional

import cohere
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


class KeywordResearchService:
    """
    Service for keyword research and topic modeling using Cohere API.
    Implements the Cohere cookbook for fueling generative content with keyword research.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "command-a-03-2025"):
        """
        Initialize the Keyword Research Service.

        Args:
            api_key: Cohere API key (defaults to environment variable)
            model: Cohere model to use for chat
        """
        self.api_key = api_key or os.getenv('COHERE_API_KEY')
        if not self.api_key:
            raise ValueError("COHERE_API_KEY must be set")

        self.co = cohere.Client(self.api_key)
        self.model = model

    def load_keywords_from_csv(self, filepath: str) -> pd.DataFrame:
        """
        Load keywords from CSV file.

        Args:
            filepath: Path to CSV file with 'keyword' and 'volume' columns

        Returns:
            DataFrame with keyword data
        """
        df = pd.read_csv(filepath)

        # Standardize column names
        if 'Keyword' in df.columns:
            df.rename(columns={'Keyword': 'keyword'}, inplace=True)
        if 'Volume' in df.columns:
            df.rename(columns={'Volume': 'volume'}, inplace=True)

        # Validate required columns
        if 'keyword' not in df.columns or 'volume' not in df.columns:
            raise ValueError("CSV must contain 'keyword' and 'volume' columns")

        return df

    def embed_keywords(self, keywords: List[str]) -> np.ndarray:
        """
        Generate embeddings for keywords using Cohere Embed.

        Args:
            keywords: List of keyword strings

        Returns:
            NumPy array of embeddings
        """
        response = self.co.embed(
            texts=keywords,
            model='embed-english-v3.0',
            input_type="search_document"
        )
        return np.array(response.embeddings)

    def cluster_keywords(self, embeddings: np.ndarray, num_topics: int = 4) -> np.ndarray:
        """
        Cluster keywords into topics using KMeans.

        Args:
            embeddings: Keyword embeddings
            num_topics: Number of topic clusters

        Returns:
            Array of cluster labels
        """
        kmeans = KMeans(n_clusters=num_topics, random_state=42, n_init="auto")
        return kmeans.fit_predict(embeddings)

    def generate_topic_name(self, keywords: List[str]) -> str:
        """
        Generate a concise topic name for a cluster of keywords.

        Args:
            keywords: List of keywords in the cluster

        Returns:
            Generated topic name
        """
        prompt = f"""Generate a concise topic name that best represents these keywords.
Provide just the topic name and not any additional details.
Keywords: {', '.join(keywords[:15])}"""  # Limit to 15 keywords to avoid token limits

        try:
            response = self.co.chat(
                model=self.model,
                message=prompt,
                preamble=""
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating topic name: {e}")
            return f"Topic - {keywords[0][:30]}"

    def process_keywords_from_csv(self, filepath: str, num_topics: int = 4) -> Dict:
        """
        Complete keyword research pipeline from CSV file.

        Args:
            filepath: Path to keyword CSV file
            num_topics: Number of topic clusters to create

        Returns:
            Dictionary with processed results
        """
        # Load keywords
        df = self.load_keywords_from_csv(filepath)

        # Generate embeddings
        print(f"Embedding {len(df)} keywords...")
        embeddings = self.embed_keywords(df['keyword'].tolist())

        # Cluster keywords
        print(f"Clustering into {num_topics} topics...")
        df['topic'] = self.cluster_keywords(embeddings, num_topics)

        # Generate topic names
        print("Generating topic names...")
        topic_keywords = {topic: list(set(group['keyword']))
                         for topic, group in df.groupby('topic')}

        topic_names = {}
        for topic_id, keywords in topic_keywords.items():
            topic_name = self.generate_topic_name(keywords)
            topic_names[topic_id] = topic_name
            print(f"  Topic {topic_id}: {topic_name}")

        df['topic_name'] = df['topic'].map(topic_names)

        # Calculate topic statistics
        topic_summary = df.groupby(['topic', 'topic_name']).agg({
            'keyword': 'count',
            'volume': 'sum'
        }).reset_index()
        topic_summary.columns = ['topic_id', 'topic_name', 'keyword_count', 'total_volume']

        return {
            'dataframe': df,
            'topic_summary': topic_summary,
            'topic_keywords': topic_keywords,
            'topic_names': topic_names
        }

    def generate_content_ideas(self, topic_summary: pd.DataFrame) -> List[Dict]:
        """
        Generate content ideas based on topic analysis.

        Args:
            topic_summary: DataFrame with topic statistics

        Returns:
            List of content ideas with metadata
        """
        content_ideas = []

        for _, row in topic_summary.iterrows():
            prompt = f"""Generate 3 content ideas for the topic "{row['topic_name']}"
that would appeal to people searching for related keywords.
Format: Return only a JSON array of objects with title, description, and format fields."""

            try:
                response = self.co.chat(
                    model=self.model,
                    message=prompt,
                    preamble=""
                )

                content_ideas.append({
                    'topic_id': row['topic_id'],
                    'topic_name': row['topic_name'],
                    'ideas': response.text,
                    'keyword_count': row['keyword_count'],
                    'search_volume': row['total_volume']
                })
            except Exception as e:
                print(f"Error generating ideas for {row['topic_name']}: {e}")

        return content_ideas

    def export_results(self, results: Dict, output_path: str = "keyword_analysis.csv"):
        """
        Export results to CSV file.

        Args:
            results: Results dictionary from process_keywords_from_csv
            output_path: Path for output CSV file
        """
        df = results['dataframe']
        df.to_csv(output_path, index=False)
        print(f"Results exported to {output_path}")


import json
import sys

# Example usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python keywordResearchService.py <filepath_or_json> [num_topics]"}))
        sys.exit(1)

    input_arg = sys.argv[1]

    try:
        service = KeywordResearchService()

        # Check if the input is a JSON string (for content ideas)
        if input_arg.startswith('['):
            topic_summary_df = pd.read_json(input_arg)
            ideas = service.generate_content_ideas(topic_summary_df)
            print(json.dumps(ideas, indent=2))
        else: # Ass-ume it's a filepath for keyword processing
            num_topics = int(sys.argv[2]) if len(sys.argv) > 2 else 4
            results = service.process_keywords_from_csv(input_arg, num_topics)
            summary_json = results['topic_summary'].to_dict(orient='records')
            output = {
                "total_keywords": len(results['dataframe']),
                "num_topics": num_topics,
                "topic_summary": summary_json,
            }
            print(json.dumps(output, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
