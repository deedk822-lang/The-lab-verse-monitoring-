#!/usr/bin/env python3
import time
import requests
from datetime import datetime
from prometheus_client import Counter, Gauge, start_http_server
import signal
import sys

# Prometheus metrics
gdelt_events_processed = Counter('gdelt_events_processed_total', 'Total GDELT events processed')
gdelt_last_update = Gauge('gdelt_last_update_timestamp', 'Last GDELT data update timestamp')
gdelt_crisis_events = Gauge('gdelt_crisis_events', 'Crisis events by category', ['category'])
gdelt_processing_rate = Gauge('gdelt_processing_rate_mbps', 'GDELT data processing rate in MB/s')
gdelt_south_africa_events = Gauge('gdelt_south_africa_events', 'Events related to South Africa')

class GDELTMonitor:
    def __init__(self):
        self.base_url = "http://data.gdeltproject.org/gdeltv2"
        self.last_file = None
        self.running = True

    def signal_handler(self, sig, frame):
        print('\n🛑 Shutting down GDELT monitor gracefully...')
        self.running = False
        sys.exit(0)

    def fetch_latest_events(self):
        """Fetch and process latest GDELT events"""
        try:
            start_time = time.time()

            # Get master file list
            response = requests.get(f"{self.base_url}/masterfilelist.txt", timeout=30)
            response.raise_for_status()

            # Calculate processing rate
            data_size_mb = len(response.content) / (1024 * 1024)
            duration = time.time() - start_time
            rate = data_size_mb / duration if duration > 0 else 0

            # Update metrics
            gdelt_processing_rate.set(rate)
            gdelt_last_update.set(time.time())

            # Parse file list
            lines = response.text.strip().split('\n')
            latest_file = lines[-1] if lines else None

            if latest_file and latest_file != self.last_file:
                file_url = latest_file.split()[-1]
                events = self.process_gdelt_file(file_url)

                gdelt_events_processed.inc(len(events))
                self.categorize_events(events)

                self.last_file = latest_file
                print(f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processed {len(events)} events at {rate:.2f} MB/s")
            else:
                print(f"⏸️  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No new data available")

        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
        except Exception as e:
            print(f"❌ Error fetching GDELT data: {e}")

    def process_gdelt_file(self, file_url):
        """Download and parse GDELT CSV file"""
        try:
            response = requests.get(file_url, timeout=60)
            response.raise_for_status()

            lines = response.text.strip().split('\n')
            events = []
            sa_events = 0

            for line in lines[:1000]:  # Process first 1000 events
                fields = line.split('\t')
                if len(fields) > 30:
                    # Check for South Africa references
                    if any('SOUTH AFRICA' in str(fields[i]).upper() for i in [6, 16, 53] if len(fields) > i):
                        sa_events += 1

                    events.append({
                        'date': fields[1] if len(fields) > 1 else None,
                        'actor': fields[6] if len(fields) > 6 else None,
                        'event_code': fields[26] if len(fields) > 26 else None,
                        'goldstein_scale': float(fields[30]) if len(fields) > 30 and fields[30] else 0
                    })

            gdelt_south_africa_events.set(sa_events)
            return events

        except Exception as e:
            print(f"❌ Error processing file: {e}")
            return []

    def categorize_events(self, events):
        """Categorize events into crisis types"""
        categories = {
            'political': 0,
            'economic': 0,
            'security': 0,
            'humanitarian': 0
        }

        for event in events:
            event_code = event.get('event_code', '')
            goldstein = event.get('goldstein_scale', 0)

            if goldstein < -5:  # Negative events
                if event_code.startswith('14'):  # Protest
                    categories['political'] += 1
                elif event_code.startswith('18'):  # Assault
                    categories['security'] += 1
                elif event_code.startswith('19'):  # Fight
                    categories['security'] += 1
                else:
                    categories['humanitarian'] += 1

        for category, count in categories.items():
            gdelt_crisis_events.labels(category=category).set(count)

    def run(self, interval=300):
        """Run monitor continuously"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        print("🌍 Vaal AI Empire - GDELT Crisis Monitor")
        print("=" * 50)
        print(f"📊 Metrics: http://localhost:9091/metrics")
        print(f"🔄 Update interval: {interval}s")
        print(f"🚀 Starting monitoring...")
        print("=" * 50)

        start_http_server(9091)

        while self.running:
            try:
                self.fetch_latest_events()
                time.sleep(interval)
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    monitor = GDELTMonitor()
    monitor.run(interval=300)  # 5 minutes
