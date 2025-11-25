import requests
import json
import os

# --- CONFIGURATION ---
# GDELT V2 GKG (Global Knowledge Graph) API endpoint. This is a public, factual endpoint.
GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# GDELT themes related to hardship, poverty, and displacement.
# These are official GDELT themes.
DISTRESS_THEMES = [
    "TAX_FNCACT_REFUGEE", "WB_2749_FOOD_CRISIS", "UNGP_FORCED_DISPLACEMENT",
    "TAX_ETHNICVIOLENCE", "CRISISLEX_C07_INSECURITY", "POVERTY"
]

def find_events_of_hardship():
    """
    Queries the GDELT API to find recent news articles in Africa
    matching themes of hardship.
    """
    print("[TAX COLLECTOR] Searching for real-world hardship events in Africa...")

    # Build a complex query for GDELT
    # We are looking for articles with any of our distress themes, sourced from Africa.
    query_params = {
        "query": f"({' OR '.join(DISTRESS_THEMES)}) sourcecountry:AF",
        "mode": "artlist",
        "maxrecords": 10, # Limit to the 10 most recent articles to keep it focused
        "format": "json",
        "sort": "DateDesc"
    }

    try:
        response = requests.get(GDELT_API_URL, params=query_params)
        response.raise_for_status() # Raises an HTTPError for bad responses
        data = response.json()

        if 'articles' not in data or not data['articles']:
            print("[TAX COLLECTOR] No recent articles matching distress themes found.")
            return None

        print(f"[TAX COLLECTOR] Found {len(data['articles'])} potential articles for review.")
        # Select the most recent and relevant article
        top_article = data['articles'][0]

        report = {
            "source": "GDELT",
            "title": top_article.get('title'),
            "url": top_article.get('url'),
            "domain": top_article.get('domain'),
            "date": top_article.get('seendate'),
            "summary": "A real-world news article has been identified indicating hardship. The next step is to use a Judge model (e.g., Command R+) to analyze the article content and propose a specific, micro-intervention action."
        }

        return report

    except requests.exceptions.RequestException as e:
        print(f"[FATAL] Could not connect to GDELT API: {e}")
        return None

def main():
    """
    Main execution function for the Tax Collector script.
    """
    report = find_events_of_hardship()

    if report:
        # This output is designed to be captured by a GitHub Action.
        # We will save it to a file that can be used as an artifact or input for the next step.
        output_path = os.getenv('GITHUB_WORKSPACE', '.') + '/tax_collector_report.json'
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"[SUCCESS] Tax Collector report generated and saved to {output_path}")
        print("--- REPORT PREVIEW ---")
        print(json.dumps(report, indent=2))
        print("----------------------")
    else:
        print("[INFO] Tax Collector run complete. No actionable report generated.")

if __name__ == "__main__":
    # The original conflict was resolved by keeping the main() call, as the Tax branch's logic 
    # was incomplete (calling an undefined function 'collect_tax').
    main()
