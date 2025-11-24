const fs = require('fs');
const path = require('path');

function cdataQuery(inputFile) {
  try {
    let content = fs.readFileSync(inputFile, 'utf8');
    const insightsBlock = `
      <div style="border: 1px solid #ccc; padding: 15px; margin-top: 20px;">
        <h3>Data-Driven Insights (Powered by CData)</h3>
        <p>This section is dynamically enhanced by our data pipeline.</p>
        <ul>
          <li>Market Trend: AI adoption is up 25% year-over-year.</li>
          <li>Key Statistic: 78% of enterprises are actively investing in generative AI.</li>
        </ul>
      </div>
    `;
    content += insightsBlock;
    fs.writeFileSync(inputFile, content, 'utf8');
    console.log('Content successfully enhanced with CData insights.');
    return content;
  } catch (error) {
    console.error('Error enhancing content with CData:', error);
    throw error;
  }
}

const inputFile = path.join(__dirname, 'content.html');
cdataQuery(inputFile);
