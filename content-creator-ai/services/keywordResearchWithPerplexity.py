import argparse
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import cohere
import numpy as np
import pandas as pd
import requests
from sklearn.cluster import KMeans


class EnhancedKeywordResearchService:
    """
    Advanced keyword research service combining Cohere embeddings/clustering
    with Perplexity's deep search for comprehensive content intelligence.
    """

    def __init__(
        self,
        cohere_key: Optional[str] = None,
        perplexity_key: Optional[str] = None,
        cohere_model: str = "command-r-plus-08-2024",
        perplexity_model: str = "llama-3.1-sonar-large-128k-online"
    ):
        """
        Initialize the Enhanced Keyword Research Service.

        Args:
            cohere_key: Cohere API key
            perplexity_key: Perplexity API key
            cohere_model: Cohere chat model
            perplexity_model: Perplexity model (online for real-time search)
        """
        self.cohere_key = cohere_key or os.getenv('COHERE_API_KEY')
        self.perplexity_key = perplexity_key or os.getenv('PERPLEXITY_API_KEY')

        if not self.cohere_key:
            raise ValueError("COHERE_API_KEY must be set")
        if not self.perplexity_key:
            raise ValueError("PERPLEXITY_API_KEY must be set")

        self.co = cohere.Client(self.cohere_key)
        self.cohere_model = cohere_model
        self.perplexity_model = perplexity_model
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"

    def load_keywords_from_csv(self, filepath: str) -> pd.DataFrame:
        """Load and validate keyword CSV."""
        df = pd.read_csv(filepath)

        # Standardize columns
        column_mapping = {
            'Keyword': 'keyword',
            'Volume': 'volume',
            'Search Volume': 'volume'
        }
        df.rename(columns=column_mapping, inplace=True)

        if 'keyword' not in df.columns or 'volume' not in df.columns:
            raise ValueError("CSV must contain 'keyword' and 'volume' columns")

        return df

    def embed_keywords(self, keywords: List[str]) -> np.ndarray:
        """Generate embeddings using Cohere."""
        response = self.co.embed(
            texts=keywords,
            model='embed-english-v3.0',
            input_type="search_document"
        )
        return np.array(response.embeddings)

    def cluster_keywords(self, embeddings: np.ndarray, num_topics: int = 4) -> np.ndarray:
        """Cluster keywords into topics."""
        kmeans = KMeans(n_clusters=num_topics, random_state=42, n_init="auto")
        return kmeans.fit_predict(embeddings)

    def generate_topic_name(self, keywords: List[str]) -> str:
        """Generate topic name using Cohere."""
        prompt = f"""Generate a concise, SEO-friendly topic name (3-5 words) that represents these keywords.
Provide ONLY the topic name, nothing else.

Keywords: {', '.join(keywords[:20])}"""

        try:
            response = self.co.chat(
                model=self.cohere_model,
                message=prompt,
                temperature=0.3
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating topic name: {e}")
            return f"Topic: {keywords[0][:30]}"

    def deep_search_topic(self, topic_name: str, keywords: List[str], search_volume: int) -> Dict:
        """
        Use Perplexity to perform deep search on a topic cluster.

        Args:
            topic_name: Generated topic name
            keywords: List of keywords in cluster
            search_volume: Total search volume

        Returns:
            Dictionary with deep search insights
        """
        # Construct comprehensive research prompt
        prompt = f"""Analyze the topic "{topic_name}" based on these high-traffic keywords: {', '.join(keywords[:15])}.

Provide a comprehensive analysis in JSON format with these exact keys:

{{
  "current_trends": "Brief description of current trends and interest patterns",
  "search_intent": "Primary user intent (informational/transactional/navigational) and what users want",
  "content_gaps": ["gap 1", "gap 2", "gap 3"],
  "top_questions": ["question 1", "question 2", "question 3", "question 4", "question 5"],
  "recommended_formats": ["format 1", "format 2", "format 3"],
  "competitive_landscape": "Overview of existing content quality and competition level",
  "unique_angles": ["angle 1", "angle 2", "angle 3"],
  "target_audience": "Primary audience demographics and expertise level",
  "seasonal_patterns": "Any seasonal trends or timing considerations",
  "related_topics": ["topic 1", "topic 2", "topic 3"]
}}

Focus on actionable insights for content creation. Search volume: {search_volume}/month"""

        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.perplexity_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert SEO and content strategist. Provide detailed, actionable insights based on real-time web data. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 2000
            }

            response = requests.post(
                self.perplexity_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Parse the response content
            content = result['choices'][0]['message']['content']

            # Try to extract JSON from response
            try:
                # Look for JSON in markdown code blocks
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.rfind('```')
                    json_str = content[json_start:json_end].strip()
                elif '```' in content:
                    json_start = content.find('```') + 3
                    json_end = content.rfind('```')
                    json_str = content[json_start:json_end].strip()
                else:
                    json_str = content

                insights = json.loads(json_str)
            except json.JSONDecodeError:
                # Fallback: return raw content
                insights = {
                    "raw_response": content,
                    "current_trends": "Analysis available in raw response",
                    "search_intent": "See full analysis",
                    "content_gaps": [],
                    "top_questions": [],
                    "recommended_formats": ["Blog post", "Guide", "Tutorial"]
                }

            # Add metadata
            insights['search_timestamp'] = datetime.utcnow().isoformat()
            insights['citations'] = result.get('citations', [])

            return insights

        except requests.exceptions.RequestException as e:
            print(f"Perplexity API error for topic '{topic_name}': {e}")
            return {
                "error": str(e),
                "current_trends": "Unable to fetch",
                "search_intent": "Unknown",
                "content_gaps": [],
                "top_questions": [],
                "recommended_formats": ["Blog post"]
            }
        except Exception as e:
            print(f"Unexpected error in deep search: {e}")
            return {
                "error": str(e),
                "current_trends": "Error occurred",
                "search_intent": "Unknown",
                "content_gaps": [],
                "top_questions": [],
                "recommended_formats": []
            }

    def generate_content_brief(
        self,
        topic_name: str,
        keywords: List[str],
        perplexity_insights: Dict
    ) -> Dict:
        """
        Generate a detailed content brief using Cohere based on Perplexity insights.
        """
        prompt = f"""Create a detailed content brief for: "{topic_name}"

Target Keywords: {', '.join(keywords[:10])}
Search Intent: {perplexity_insights.get('search_intent', 'Unknown')}
Content Gaps: {', '.join(perplexity_insights.get('content_gaps', []))}
Top Questions: {', '.join(perplexity_insights.get('top_questions', [])[:3])}

Generate a content brief with:
1. Compelling headline (H1)
2. Detailed outline with H2/H3 structure
3. Recommended word count
4. Key points to cover
5. Target audience
6. Call-to-action suggestions

Format as JSON with keys: title, outline (array), word_count, key_points (array), target_audience, cta_suggestions (array)"""

        try:
            response = self.co.chat(
                model=self.cohere_model,
                message=prompt,
                temperature=0.4
            )

            # Try to parse JSON response
            content = response.text
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.rfind('```')
                json_str = content[json_start:json_end].strip()
                brief = json.loads(json_str)
            else:
                brief = {
                    "title": f"Complete Guide to {topic_name}",
                    "outline": ["Introduction", "Main Content", "Conclusion"],
                    "word_count": 2000,
                    "key_points": keywords[:5],
                    "target_audience": "General audience",
                    "cta_suggestions": ["Learn more", "Get started"]
                }

            return brief

        except Exception as e:
            print(f"Error generating content brief: {e}")
            return {
                "title": topic_name,
                "outline": ["Introduction", "Main Body", "Conclusion"],
                "word_count": 1500,
                "key_points": keywords[:5],
                "target_audience": "General",
                "cta_suggestions": []
            }

    def process_keywords_with_deep_search(
        self,
        csv_path: str,
        num_topics: int = 4,
        enable_deep_search: bool = True,
        deep_search_top_n: int = 3
    ) -> Dict:
        """
        Complete pipeline: keyword clustering + Perplexity deep search.

        Args:
            csv_path: Path to keyword CSV
            num_topics: Number of topic clusters
            enable_deep_search: Whether to use Perplexity deep search
            deep_search_top_n: Number of top topics to deep search (cost control)

        Returns:
            Comprehensive results dictionary
        """
        print("🚀 Starting enhanced keyword research pipeline...")

        # Step 1: Load keywords
        print(f"📊 Loading keywords from {csv_path}...")
        df = self.load_keywords_from_csv(csv_path)
        total_keywords = len(df)
        print(f"   Loaded {total_keywords} keywords")

        # Step 2: Embed keywords
        print("🧬 Generating embeddings with Cohere...")
        embeddings = self.embed_keywords(df['keyword'].tolist())
        print(f"   Created {embeddings.shape[0]}x{embeddings.shape[1]} embedding matrix")

        # Step 3: Cluster
        print(f"🎯 Clustering into {num_topics} topics...")
        df['topic'] = self.cluster_keywords(embeddings, num_topics)

        # Step 4: Generate topic names
        print("📝 Generating topic names with Cohere...")
        topic_keywords = {topic: list(set(group['keyword']))
                         for topic, group in df.groupby('topic')}

        topic_names = {}
        for topic_id, keywords in topic_keywords.items():
            topic_name = self.generate_topic_name(keywords)
            topic_names[topic_id] = topic_name
            print(f"   Topic {topic_id}: {topic_name}")

        df['topic_name'] = df['topic'].map(topic_names)

        # Step 5: Calculate topic stats
        topic_summary = df.groupby(['topic', 'topic_name']).agg({
            'keyword': 'count',
            'volume': 'sum'
        }).reset_index()
        topic_summary.columns = ['topic_id', 'topic_name', 'keyword_count', 'total_volume']
        topic_summary = topic_summary.sort_values('total_volume', ascending=False)

        # Step 6: Perplexity Deep Search (top N topics)
        enriched_topics = []

        if enable_deep_search:
            print(f"\n🔍 Performing Perplexity deep search on top {deep_search_top_n} topics...")

            for idx, row in topic_summary.head(deep_search_top_n).iterrows():
                topic_id = row['topic_id']
                topic_name = row['topic_name']
                keywords = topic_keywords[topic_id]

                print(f"\n   Researching: {topic_name} ({row['keyword_count']} keywords, {row['total_volume']:,} volume)")

                # Deep search
                perplexity_insights = self.deep_search_topic(
                    topic_name,
                    keywords,
                    int(row['total_volume'])
                )

                # Generate content brief
                content_brief = self.generate_content_brief(
                    topic_name,
                    keywords,
                    perplexity_insights
                )

                enriched_topics.append({
                    'topic_id': topic_id,
                    'topic_name': topic_name,
                    'keywords': keywords,
                    'keyword_count': row['keyword_count'],
                    'total_volume': int(row['total_volume']),
                    'perplexity_insights': perplexity_insights,
                    'content_brief': content_brief
                })

                print("   ✅ Complete")

        print("\n✨ Pipeline complete!")

        return {
            'dataframe': df.to_dict(orient='records'),
            'topic_summary': topic_summary.to_dict(orient='records'),
            'topic_keywords': topic_keywords,
            'topic_names': topic_names,
            'enriched_topics': enriched_topics,
            'summary': {
                'total_keywords': total_keywords,
                'num_topics': num_topics,
                'total_volume': int(df['volume'].sum()),
                'deep_searched_topics': len(enriched_topics),
                'timestamp': datetime.utcnow().isoformat()
            }
        }

    def export_results(
        self,
        results: Dict,
        output_dir: str = "keyword_research_output"
    ):
        """
        Export all results to organized files.
        """
        os.makedirs(output_dir, exist_ok=True)

        # Export main dataframe
        df_path = os.path.join(output_dir, "keyword_clusters.csv")
        pd.DataFrame(results['dataframe']).to_csv(df_path, index=False)
        print(f"📄 Exported: {df_path}")

        # Export topic summary
        summary_path = os.path.join(output_dir, "topic_summary.csv")
        pd.DataFrame(results['topic_summary']).to_csv(summary_path, index=False)
        print(f"📄 Exported: {summary_path}")

        # Export enriched topics as JSON
        if results['enriched_topics']:
            enriched_path = os.path.join(output_dir, "enriched_topics.json")
            with open(enriched_path, 'w') as f:
                json.dump(results['enriched_topics'], f, indent=2)
            print(f"📄 Exported: {enriched_path}")

            # Export individual content briefs
            briefs_dir = os.path.join(output_dir, "content_briefs")
            os.makedirs(briefs_dir, exist_ok=True)

            for topic in results['enriched_topics']:
                brief_filename = f"{topic['topic_name'].replace(' ', '_').lower()}_brief.json"
                brief_path = os.path.join(briefs_dir, brief_filename)

                with open(brief_path, 'w') as f:
                    json.dump({
                        'topic': topic['topic_name'],
                        'keywords': topic['keywords'],
                        'volume': topic['total_volume'],
                        'insights': topic['perplexity_insights'],
                        'brief': topic['content_brief']
                    }, f, indent=2)

            print(f"📁 Exported {len(results['enriched_topics'])} content briefs to: {briefs_dir}")

        # Export summary report
        report_path = os.path.join(output_dir, "research_summary.json")
        with open(report_path, 'w') as f:
            json.dump(results['summary'], f, indent=2)
        print(f"📄 Exported: {report_path}")

        print(f"\n✅ All files exported to: {output_dir}")


# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced Keyword Research with Perplexity Deep Search")
    parser.add_argument('--csv-path', type=str, required=True, help='Path to the keyword CSV file')
    parser.add_argument('--num-topics', type=int, default=4, help='Number of topic clusters to create')
    parser.add_argument('--enable-deep-search', type=bool, default=True, help='Enable Perplexity deep search')
    parser.add_argument('--deep-search-top-n', type=int, default=3, help='Number of top topics to deep search')

    args = parser.parse_args()

    # Initialize service
    service = EnhancedKeywordResearchService()

    # Process with deep search
    results = service.process_keywords_with_deep_search(
        csv_path=args.csv_path,
        num_topics=args.num_topics,
        enable_deep_search=args.enable_deep_search,
        deep_search_top_n=args.deep_search_top_n
    )

    print(json.dumps(results))
