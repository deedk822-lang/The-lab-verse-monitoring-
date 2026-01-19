
import sys
from src.products.content_studio import ContentStudio

print('🎨 ACTIVATING CONTENT FACTORY...')
studio = ContentStudio()

if studio.client:
    # Real Generation via Hugging Face
    res = studio.generate_social_bundle('Tech Startup', 'AI Automation in South Africa')
    print(f'✅ ASSET GENERATED: {res}')
else:
    print('❌ Studio Offline (Check HF Key)')
    sys.exit(1)
