const { AccessAnalyzer } = require('@alicloud/accessanalyzer20200901');
const { Credential } = require('@alicloud/credentials');
const OpenApi = require('@alicloud/openapi-client');
const Util = require('@alicloud/tea-util');
const fs = require('fs');

class AlibabaCloudSecurityScanner {
  constructor() {
    // Initialize client with environment variables
    const config = new OpenApi.Config({
      accessKeyId: process.env.ALIBABA_CLOUD_ACCESS_KEY_ID,
      accessKeySecret: process.env.ALIBABA_CLOUD_SECRET_KEY,
      endpoint: process.env.ALIBABA_CLOUD_ENDPOINT || 'accessanalyzer.cn-hangzhou.aliyuncs.com',
      regionId: process.env.ALIBABA_CLOUD_REGION_ID || 'cn-hangzhou'
    });

    this.client = new AccessAnalyzer(config);
  }

  async listAnalyzers() {
    try {
      const runtime = new Util.RuntimeOptions({});
      const response = await this.client.listAnalyzersWithOptions({}, runtime);
      return response.body.analyzers;
    } catch (error) {
      console.error('Error listing analyzers:', error);
      throw error;
    }
  }

  async listFindings(analyzerName) {
    try {
      const request = {
        analyzerName: analyzerName,
        maxResults: 100
      };

      const runtime = new Util.RuntimeOptions({});
      const response = await this.client.listFindingsWithOptions(request, {}, runtime);
      return response.body.findings;
    } catch (error) {
      console.error('Error listing findings:', error);
      throw error;
    }
  }

  async runSecurityAnalysis() {
    console.log('Starting Alibaba Cloud security analysis...');

    try {
      // Get all analyzers
      const analyzers = await this.listAnalyzers();
      console.log(`Found ${analyzers.length} analyzers`);

      let allFindings = [];

      // Get findings for each analyzer
      for (const analyzer of analyzers) {
        console.log(`Analyzing ${analyzer.name} (${analyzer.type})...`);
        const findings = await this.listFindings(analyzer.name);
        allFindings.push(...findings.map(finding => ({
          ...finding,
          analyzerName: analyzer.name,
          analyzerType: analyzer.type
        })));
      }

      // Generate SARIF report
      const sarifReport = {
        version: "2.1.0",
        $schema: "https://json.schemastore.org/sarif-2.1.0.json",
        runs: [
          {
            tool: {
              driver: {
                name: "Alibaba Cloud Access Analyzer",
                informationUri: "https://www.alibabacloud.com/product/access-analyzer",
                fullName: "Alibaba Cloud Access Analyzer Security Scanner"
              }
            },
            results: [],
            invocations: [
              {
                startTimeUtc: new Date().toISOString(),
                executionSuccessful: true
              }
            ]
          }
        ]
      };

      // Add findings to SARIF report
      for (const finding of allFindings) {
        const result = {
          ruleId: `access-analyzer-${finding.severity.toLowerCase()}`,
          level: this.getLevelFromSeverity(finding.severity),
          message: {
            text: `Access analyzer finding: ${finding.id} - Resource: ${finding.resource}, Status: ${finding.status}`
          },
          locations: [
            {
              physicalLocation: {
                artifactLocation: {
                  uri: finding.resource
                }
              }
            }
          ],
          properties: {
            createdAt: finding.createdAt,
            analyzerName: finding.analyzerName,
            analyzerType: finding.analyzerType,
            principal: finding.principal,
            condition: finding.condition
          }
        };
        sarifReport.runs[0].results.push(result);
      }

      // Save report
      const outputPath = 'security-report.json';
      fs.writeFileSync(outputPath, JSON.stringify(sarifReport, null, 2));
      console.log(`Security analysis completed. Report saved to ${outputPath}`);

      // Print summary
      console.log(`\nScan Summary:`);
      console.log(`- Total Findings: ${allFindings.length}`);

      const criticalFindings = allFindings.filter(f => f.severity === 'CRITICAL');
      const highFindings = allFindings.filter(f => f.severity === 'HIGH');

      console.log(`- Critical Findings: ${criticalFindings.length}`);
      console.log(`- High Findings: ${highFindings.length}`);

      if (criticalFindings.length > 0 || highFindings.length > 0) {
        console.log(`- Total Critical/High issues: ${criticalFindings.length + highFindings.length}`);
        return 1; // Return error code if critical/high issues found
      }

      return 0;
    } catch (error) {
      console.error('Security scan failed:', error);
      return 1;
    }
  }

  getLevelFromSeverity(severity) {
    const severityMap = {
      'CRITICAL': 'error',
      'HIGH': 'error',
      'MEDIUM': 'warning',
      'LOW': 'note',
      'INFO': 'note'
    };
    return severityMap[severity.toUpperCase()] || 'note';
  }
}

async function main() {
  const scanner = new AlibabaCloudSecurityScanner();
  const exitCode = await scanner.runSecurityAnalysis();
  process.exit(exitCode);
}

if (require.main === module) {
  main().catch(err => {
    console.error('Uncaught error:', err);
    process.exit(1);
  });
}

module.exports = AlibabaCloudSecurityScanner;

echo "Complete repository setup with GLM-4.7 and AutoGLM integration completed!"
echo ""
echo "Key features implemented:"
echo "- GLM-4.7 integration with advanced reasoning capabilities"
echo "- AutoGLM autonomous orchestrator with security analysis"
echo "- Complete API endpoints including http://localhost:3000/api/test/health"
echo "- Alibaba Cloud Access Analyzer integration"
echo "- All existing repository functionality preserved"
echo ""
echo "Next steps:"
echo "1. Run 'npm install' to install all dependencies"
echo "2. Update .env with your API keys (especially ZAI_API_KEY for GLM)"
echo "3. Run 'npm start' to start the server"
echo "4. Test the health endpoint at http://localhost:3000/api/test/health"
echo "5. Try GLM functionality with 'npm run glm-test'"
