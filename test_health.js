const axios = require('axios');

async function testHealthEndpoint() {
  try {
    const response = await axios.get('http://localhost:3000/api/test/health');
    console.log('✅ Health check successful!');
    console.log('Response:', JSON.stringify(response.data, null, 2));
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
    }
  }
}

testHealthEndpoint();
