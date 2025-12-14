#!/usr/bin/env python3
"""
Kaggle Intelligence Pipeline
Identity: Lungelo Luda (lungeloluda) - Data Analyst
Email: dimakatsomoleli@gmail.com

Syncs Kaggle datasets, creates market insights, and stores in OSS
Part of Vaal AI Empire - Intelligence Division

Run: Daily at 6 AM SAST via GitHub Actions
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add vaal-ai-empire to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_environment():
    """Verify all required environment variables are set"""
    print("🔐 Checking environment variables...")
    
    required_vars = {
        'KAGGLE_USERNAME': 'Kaggle username (lungeloluda)',
        'KAGGLE_KEY': 'Kaggle API key',
        'JIRA_BASE_URL': 'Jira base URL',
        'JIRA_USER_EMAIL': 'Jira user email (dimakatsomoleli@gmail.com)',
        'JIRA_API_TOKEN': 'Jira API token',
        'OSS_ACCESS_KEY_ID': 'Alibaba OSS Access Key',
        'OSS_ACCESS_KEY_SECRET': 'Alibaba OSS Secret',
        'OSS_ENDPOINT': 'Alibaba OSS Endpoint',
        'OSS_BUCKET': 'Alibaba OSS Bucket'
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  ❌ {var} ({description})")
        else:
            # Mask sensitive values in output
            if var in ['KAGGLE_KEY', 'JIRA_API_TOKEN', 'OSS_ACCESS_KEY_SECRET']:
                print(f"  ✅ {var} (configured)")
            else:
                print(f"  ✅ {var}: {os.getenv(var)}")
    
    if missing:
        print("\n⚠️  Missing required environment variables:")
        print("\n".join(missing))
        return False
    
    print("✅ All environment variables configured!\n")
    return True


def setup_kaggle_credentials():
    """Create Kaggle credentials file from environment variables"""
    print("📁 Setting up Kaggle credentials for: lungeloluda...")
    
    kaggle_dir = Path.home() / '.kaggle'
    kaggle_dir.mkdir(exist_ok=True, parents=True)
    
    credentials = {
        'username': os.getenv('KAGGLE_USERNAME'),
        'key': os.getenv('KAGGLE_KEY')
    }
    
    credentials_file = kaggle_dir / 'kaggle.json'
    with open(credentials_file, 'w') as f:
        json.dump(credentials, f)
    
    # Set proper permissions (Kaggle requires 600)
    credentials_file.chmod(0o600)
    
    print(f"✅ Kaggle credentials saved for: {credentials['username']}")
    print(f"   📧 Associated email: dimakatsomoleli@gmail.com\n")


def fetch_trending_datasets():
    """Fetch trending datasets from Kaggle relevant to SA market"""
    print("📊 Fetching trending Kaggle datasets...")
    
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        api = KaggleApi()
        api.authenticate()
        
        # Search for datasets relevant to South African business intelligence
        search_terms = [
            'south africa',
            'financial analysis',
            'market trends',
            'consumer behavior',
            'economic data'
        ]
        
        datasets = []
        for term in search_terms[:2]:  # Limit to 2 searches to avoid rate limits
            print(f"  🔍 Searching for: {term}")
            try:
                results = api.dataset_list(search=term, page=1)
                datasets.extend(results[:3])  # Top 3 from each search
            except Exception as e:
                print(f"  ⚠️  Search failed for '{term}': {e}")
        
        print(f"✅ Found {len(datasets)} relevant datasets\n")
        return datasets
        
    except Exception as e:
        print(f"⚠️  Error fetching datasets: {e}")
        print("   Continuing with empty dataset list...")
        return []


def analyze_dataset_value(dataset):
    """Analyze potential business value of a dataset"""
    print(f"🔬 Analyzing: {dataset.ref}")
    
    # Simple scoring based on metadata
    score = 0
    insights = []
    
    # Check download count
    if hasattr(dataset, 'downloadCount') and dataset.downloadCount:
        if dataset.downloadCount > 10000:
            score += 3
            insights.append(f"High popularity ({dataset.downloadCount:,} downloads)")
        elif dataset.downloadCount > 1000:
            score += 2
            insights.append(f"Moderate popularity ({dataset.downloadCount:,} downloads)")
    
    # Check vote count
    if hasattr(dataset, 'voteCount') and dataset.voteCount:
        if dataset.voteCount > 100:
            score += 2
            insights.append(f"Well-received ({dataset.voteCount} votes)")
    
    # Check size
    if hasattr(dataset, 'size') and dataset.size:
        if dataset.size > 1000000:  # > 1MB
            score += 1
            insights.append("Substantial data volume")
    
    return {
        'dataset_ref': dataset.ref,
        'title': dataset.title if hasattr(dataset, 'title') else 'Unknown',
        'score': score,
        'insights': insights,
        'url': f"https://www.kaggle.com/{dataset.ref}"
    }


def create_jira_ticket(analysis):
    """Create Jira ticket for high-value dataset"""
    print(f"📝 Creating Jira ticket for: {analysis['title'][:50]}...")
    
    try:
        from jira import JIRA
        
        jira = JIRA(
            server=os.getenv('JIRA_BASE_URL'),
            basic_auth=(
                os.getenv('JIRA_USER_EMAIL'),
                os.getenv('JIRA_API_TOKEN')
            )
        )
        
        # Get first available project
        projects = jira.projects()
        if not projects:
            print("⚠️  No Jira projects found. Skipping ticket creation.")
            return None
        
        project_key = projects[0].key
        
        # Create issue
        issue_dict = {
            'project': {'key': project_key},
            'summary': f"Kaggle Dataset: {analysis['title'][:80]}",
            'description': f"""
*Kaggle Intelligence Pipeline - Automated Discovery*

*Discovered by:* Lungelo Luda (lungeloluda)
*Dataset:* {analysis['title']}
*URL:* {analysis['url']}
*Value Score:* {analysis['score']}/6

*Insights:*
{chr(10).join('• ' + insight for insight in analysis['insights'])}

*Recommended Actions:*
1. Review dataset for potential use in Vaal AI Empire products
2. Assess data quality and licensing
3. Consider integration with Tax Collector or JSE Specialist agents
4. Evaluate for R25,000 market research reports

_Auto-generated by Kaggle Intelligence Pipeline_
_Identity: Lungelo Luda (dimakatsomoleli@gmail.com)_
_Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M SAST')}_
""",
            'issuetype': {'name': 'Task'},
        }
        
        new_issue = jira.create_issue(fields=issue_dict)
        print(f"✅ Created Jira ticket: {new_issue.key}\n")
        return new_issue.key
        
    except Exception as e:
        print(f"⚠️  Error creating Jira ticket: {e}")
        return None


def upload_to_oss(analysis_results):
    """Upload analysis results to Alibaba OSS"""
    print("☁️  Uploading results to OSS...")
    
    try:
        import oss2
        
        auth = oss2.Auth(
            os.getenv('OSS_ACCESS_KEY_ID'),
            os.getenv('OSS_ACCESS_KEY_SECRET')
        )
        
        bucket = oss2.Bucket(
            auth,
            os.getenv('OSS_ENDPOINT'),
            os.getenv('OSS_BUCKET')
        )
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"kaggle-intelligence/{timestamp}_lungeloluda_analysis.json"
        
        # Upload
        content = json.dumps(analysis_results, indent=2)
        bucket.put_object(filename, content)
        
        print(f"✅ Uploaded to OSS: {filename}\n")
        return filename
        
    except Exception as e:
        print(f"⚠️  Error uploading to OSS: {e}")
        return None


def main():
    """Main execution pipeline"""
    print("=" * 70)
    print("🚀 KAGGLE INTELLIGENCE PIPELINE - STARTING")
    print(f"   Identity: Lungelo Luda (lungeloluda)")
    print(f"   Email: dimakatsomoleli@gmail.com")
    print(f"   Executed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S SAST')}")
    print("=" * 70)
    print()
    
    # Step 1: Environment check
    if not check_environment():
        print("❌ Environment check failed. Exiting.")
        return 1
    
    # Step 2: Setup Kaggle credentials
    try:
        setup_kaggle_credentials()
    except Exception as e:
        print(f"❌ Failed to setup Kaggle credentials: {e}")
        return 1
    
    # Step 3: Fetch datasets
    datasets = fetch_trending_datasets()
    if not datasets:
        print("⚠️  No datasets found. Creating summary and exiting gracefully.")
        
        # Create empty result for tracking
        results = {
            'timestamp': datetime.now().isoformat(),
            'identity': 'lungeloluda',
            'email': 'dimakatsomoleli@gmail.com',
            'datasets_analyzed': 0,
            'high_value_datasets': 0,
            'analyses': [],
            'status': 'no_datasets_found'
        }
        upload_to_oss(results)
        
        print("=" * 70)
        print("✅ Kaggle Intelligence Pipeline - COMPLETED (NO DATA)")
        print("=" * 70)
        return 0
    
    # Step 4: Analyze datasets
    print("🔬 Analyzing datasets for business value...")
    analyses = []
    jira_tickets_created = 0
    
    for dataset in datasets:
        try:
            analysis = analyze_dataset_value(dataset)
            analyses.append(analysis)
            
            # Create Jira ticket for high-value datasets (score >= 4)
            if analysis['score'] >= 4:
                ticket = create_jira_ticket(analysis)
                if ticket:
                    jira_tickets_created += 1
        except Exception as e:
            print(f"⚠️  Error analyzing dataset: {e}")
    
    print(f"✅ Analyzed {len(analyses)} datasets")
    print(f"📝 Created {jira_tickets_created} Jira tickets\n")
    
    # Step 5: Upload results to OSS
    results = {
        'timestamp': datetime.now().isoformat(),
        'identity': 'lungeloluda',
        'email': 'dimakatsomoleli@gmail.com',
        'datasets_analyzed': len(analyses),
        'high_value_datasets': len([a for a in analyses if a['score'] >= 4]),
        'jira_tickets_created': jira_tickets_created,
        'analyses': analyses,
        'status': 'success'
    }
    
    upload_to_oss(results)
    
    # Final summary
    print("=" * 70)
    print("✅ KAGGLE INTELLIGENCE PIPELINE - COMPLETED")
    print(f"   Identity: Lungelo Luda (lungeloluda)")
    print(f"   Total datasets analyzed: {len(analyses)}")
    print(f"   High-value datasets found: {len([a for a in analyses if a['score'] >= 4])}")
    print(f"   Jira tickets created: {jira_tickets_created}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
