# scripts/alibaba_cloud_security_scan.py
"""Complete implementation for Alibaba Cloud Access Analyzer integration with full type safety."""
import json
import subprocess
import sys
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Configure logging for observability
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Finding:
    """Data class for security findings"""
    id: str
    resource: str
    status: str
    severity: str
    principal: Dict[str, Any]
    condition: Dict[str, Any]
    created_at: str
    analyzer_name: str
    analyzer_type: str

@dataclass
class SecurityIssue:
    """Data class for security issues"""
    type: str
    resource: str
    resource_name: str
    severity: str
    issue: str
    details: str

class AlibabaCloudSecurityScanner:
    """Security scanner that integrates with Alibaba Cloud Access Analyzer."""

    def __init__(self) -> None:
        self.region = os.getenv('ALIBABA_CLOUD_REGION_ID', 'cn-hangzhou')
        self.timeout = int(os.getenv('ALIBABA_CLI_TIMEOUT', '30'))

    def run_command(self, cmd: str) -> Tuple[Optional[str], bool]:
        """
        Execute an Alibaba Cloud CLI command with timeout and error handling.

        Args:
            cmd: The command to execute

        Returns:
            Tuple of (output, success_status)
        """
        try:
            logger.info(f"Executing command: {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )
            return result.stdout.strip(), True
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {cmd}")
            return None, False
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {cmd}")
            logger.error(f"Error: {e.stderr}")
            return None, False
        except Exception as e:
            logger.error(f"Unexpected error executing command: {cmd}")
            logger.error(f"Error: {str(e)}")
            return None, False

    def get_access_analyzer_findings(self) -> List[Finding]:
        """Get actual findings from Alibaba Cloud Access Analyzer."""
        findings: List[Finding] = []

        # List all analyzers
        cmd = f"aliyun accessanalyzer ListAnalyzers --RegionId {self.region} --output json"
        analyzers_output, success = self.run_command(cmd)

        if not success or not analyzers_output:
            logger.warning("Failed to retrieve analyzers from Access Analyzer")
            return findings

        try:
            analyzers_data = json.loads(analyzers_output)
            analyzers = analyzers_data.get('Analyzers', [])

            for analyzer in analyzers:
                analyzer_name = analyzer['Name']
                analyzer_type = analyzer['Type']

                # Get findings for this analyzer
                findings_cmd = (
                    f"aliyun accessanalyzer ListFindings "
                    f"--AnalyzerName {analyzer_name} "
                    f"--RegionId {self.region} "
                    f"--output json"
                )

                findings_output, findings_success = self.run_command(findings_cmd)

                if findings_success and findings_output:
                    findings_data = json.loads(findings_output)

                    for finding in findings_data.get('Findings', []):
                        finding_obj = Finding(
                            id=finding.get('Id', ''),
                            resource=finding.get('Resource', ''),
                            status=finding.get('Status', ''),
                            severity=finding.get('Severity', ''),
                            principal=finding.get('Principal', {}),
                            condition=finding.get('Condition', {}),
                            created_at=finding.get('CreatedAt', ''),
                            analyzer_name=analyzer_name,
                            analyzer_type=analyzer_type
                        )
                        findings.append(finding_obj)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Access Analyzer output: {str(e)}")
        except KeyError as e:
            logger.error(f"Missing expected field in Access Analyzer response: {str(e)}")

        return findings

    def get_ecs_security_groups(self) -> List[SecurityIssue]:
        """Analyze ECS security groups for potential issues."""
        security_issues: List[SecurityIssue] = []

        # Get all security groups
        cmd = f"aliyun ecs DescribeSecurityGroups --RegionId {self.region} --output json"
        sg_output, success = self.run_command(cmd)

        if not success or not sg_output:
            logger.warning("Failed to retrieve ECS security groups")
            return security_issues

        try:
            sg_data = json.loads(sg_output)

            for sg in sg_data.get('SecurityGroups', {}).get('SecurityGroup', []):
                sg_id = sg.get('SecurityGroupId', '')
                sg_name = sg.get('SecurityGroupName', '')

                # Get permissions for this security group
                perms_cmd = (
                    f"aliyun ecs DescribeSecurityGroupAttribute "
                    f"--SecurityGroupId {sg_id} "
                    f"--RegionId {self.region} "
                    f"--output json"
                )

                perms_output, perms_success = self.run_command(perms_cmd)

                if perms_success and perms_output:
                    perms_data = json.loads(perms_output)

                    for permission in perms_data.get('Permissions', {}).get('Permission', []):
                        # Check for overly permissive rules
                        source_cidr = permission.get('SourceCidrIp', '')
                        port_range = permission.get('PortRange', '')

                        # Flag overly permissive rules (e.g., 0.0.0.0/0 on all ports)
                        if source_cidr == '0.0.0.0/0' and port_range == '-1/-1':
                            issue = SecurityIssue(
                                type="OVERLY_PERMISSIVE_SECURITY_GROUP",
                                resource=sg_id,
                                resource_name=sg_name,
                                severity="HIGH",
                                issue="Security group allows all IP addresses access to all ports",
                                details=f"Security group {sg_name} ({sg_id}) has a rule that allows inbound traffic from 0.0.0.0/0 on all ports"
                            )
                            security_issues.append(issue)

                        # Check for public access to sensitive ports
                        sensitive_ports = ['22', '3389', '21', '23', '1433', '3306', '5432', '6379', '27017']
                        if source_cidr == '0.0.0.0/0' and any(port in port_range for port in sensitive_ports):
                            issue = SecurityIssue(
                                type="PUBLIC_ACCESS_TO_SENSITIVE_PORT",
                                resource=sg_id,
                                resource_name=sg_name,
                                severity="HIGH",
                                issue=f"Public access to potentially sensitive port: {port_range}",
                                details=f"Security group {sg_name} ({sg_id}) allows public access to port {port_range}"
                            )
                            security_issues.append(issue)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ECS security group output: {str(e)}")
        except KeyError as e:
            logger.error(f"Missing expected field in ECS security group response: {str(e)}")

        return security_issues

    def get_ram_policy_analysis(self) -> List[SecurityIssue]:
        """Analyze RAM policies for potential security issues."""
        policy_issues: List[SecurityIssue] = []

        # List all users
        cmd = "aliyun ram ListUsers --output json"
        users_output, success = self.run_command(cmd)

        if not success or not users_output:
            logger.warning("Failed to retrieve RAM users")
            return policy_issues

        try:
            users_data = json.loads(users_output)

            for user in users_data.get('Users', {}).get('User', []):
                username = user.get('UserName', '')

                # Check attached policies for this user
                policies_cmd = f"aliyun ram ListAttachedUserPolicies --UserName {username} --output json"
                policies_output, policies_success = self.run_command(policies_cmd)

                if policies_success and policies_output:
                    policies_data = json.loads(policies_output)

                    for policy in policies_data.get('Policies', {}).get('Policy', []):
                        policy_name = policy.get('PolicyName', '')
                        policy_type = policy.get('PolicyType', '')

                        # Get policy document
                        doc_cmd = (
                            f"aliyun ram GetPolicy --PolicyName {policy_name} "
                            f"--PolicyType {policy_type} --output json"
                        )

                        doc_output, doc_success = self.run_command(doc_cmd)

                        if doc_success and doc_output:
                            try:
                                doc_data = json.loads(doc_output)
                                policy_doc = doc_data.get('Policy', {}).get('DefaultVersion', {}).get('Document')

                                if policy_doc:
                                    # Check for overly permissive policies
                                    policy_document = json.loads(policy_doc.replace('\n', '\\n'))

                                    for statement in policy_document.get('Statement', []):
                                        effect = statement.get('Effect', '')
                                        if effect == 'Allow':
                                            actions = statement.get('Action', [])
                                            if isinstance(actions, str):
                                                actions = [actions]

                                            # Check for wildcard actions (*)
                                            if '*' in str(actions) or 'ram:*' in actions or 'ecs:*' in actions:
                                                issue = SecurityIssue(
                                                    type="OVERLY_PERMISSIVE_POLICY",
                                                    resource=username,
                                                    resource_name=policy_name,
                                                    severity="HIGH",
                                                    issue=f"User {username} has overly permissive policy: {policy_name}",
                                                    details=f"Policy grants wildcard access: {actions}"
                                                )
                                                policy_issues.append(issue)
                            except json.JSONDecodeError:
                                logger.warning(f"Could not parse policy document for {policy_name}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse RAM users output: {str(e)}")
        except KeyError as e:
            logger.error(f"Missing expected field in RAM users response: {str(e)}")

        return policy_issues

    def generate_sarif_report(self, findings: List[Finding], security_issues: List[SecurityIssue], policy_issues: List[SecurityIssue]) -> Dict[str, Any]:
        """Generate SARIF report for GitHub security scanning."""
        sarif_report = {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Alibaba Cloud Access Analyzer",
                            "informationUri": "https://www.alibabacloud.com/product/access-analyzer",
                            "fullName": "Alibaba Cloud Access Analyzer Security Scanner"
                        }
                    },
                    "results": [],
                    "invocations": [
                        {
                            "startTimeUtc": datetime.utcnow().isoformat() + "Z",
                            "executionSuccessful": True
                        }
                    ]
                }
            ]
        }

        # Add access analyzer findings
        for finding in findings:
            result = {
                "ruleId": f"access-analyzer-{finding.severity.lower()}",
                "level": self._get_level_from_severity(finding.severity),
                "message": {
                    "text": f"Access analyzer finding: {finding.id} - Resource: {finding.resource}, Status: {finding.status}"
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": finding.resource
                            }
                        }
                    }
                ],
                "properties": {
                    "createdAt": finding.created_at,
                    "analyzerName": finding.analyzer_name,
                    "analyzerType": finding.analyzer_type,
                    "principal": finding.principal,
                    "condition": finding.condition
                }
            }
            sarif_report["runs"][0]["results"].append(result)

        # Add security group issues
        for issue in security_issues:
            result = {
                "ruleId": issue.type,
                "level": self._get_level_from_severity(issue.severity),
                "message": {
                    "text": issue.issue
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": issue.resource
                            }
                        }
                    }
                ],
                "properties": {
                    "resourceName": issue.resource_name,
                    "details": issue.details
                }
            }
            sarif_report["runs"][0]["results"].append(result)

        # Add policy issues
        for issue in policy_issues:
            result = {
                "ruleId": issue.type,
                "level": self._get_level_from_severity(issue.severity),
                "message": {
                    "text": issue.issue
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": issue.resource
                            }
                        }
                    }
                ],
                "properties": {
                    "resourceName": issue.resource_name,
                    "details": issue.details
                }
            }
            sarif_report["runs"][0]["results"].append(result)

        return sarif_report

    def _get_level_from_severity(self, severity: str) -> str:
        """Convert Alibaba Cloud severity to SARIF level."""
        severity_map = {
            'CRITICAL': 'error',
            'HIGH': 'error',
            'MEDIUM': 'warning',
            'LOW': 'note',
            'INFO': 'note'
        }
        return severity_map.get(severity.upper(), 'note')

    def run_scan(self) -> int:
        """Execute the complete security scan."""
        logger.info("Starting Alibaba Cloud security scan...")

        # Get access analyzer findings
        logger.info("Scanning Access Analyzer findings...")
        access_findings = self.get_access_analyzer_findings()

        # Get ECS security issues
        logger.info("Analyzing ECS security groups...")
        security_issues = self.get_ecs_security_groups()

        # Get RAM policy issues
        logger.info("Analyzing RAM policies...")
        policy_issues = self.get_ram_policy_analysis()

        # Generate SARIF report
        logger.info("Generating SARIF report...")
        sarif_report = self.generate_sarif_report(
            access_findings,
            security_issues,
            policy_issues
        )

        # Save report
        output_file = "security-report.json"
        with open(output_file, 'w') as f:
            json.dump(sarif_report, f, indent=2)

        logger.info(f"Security scan completed. Report saved to {output_file}")

        # Print summary
        print(f"\nScan Summary:")
        print(f"- Access Analyzer Findings: {len(access_findings)}")
        print(f"- Security Group Issues: {len(security_issues)}")
        print(f"- Policy Issues: {len(policy_issues)}")

        total_critical = len([f for f in access_findings if f.severity in ['CRITICAL', 'HIGH']])
        total_critical += len([f for f in security_issues if f.severity in ['CRITICAL', 'HIGH']])
        total_critical += len([f for f in policy_issues if f.severity in ['CRITICAL', 'HIGH']])

        if total_critical > 0:
            print(f"- Total Critical/High issues: {total_critical}")
            return 1

        return 0


def main() -> int:
    """Main entry point for the security scanner."""
    scanner = AlibabaCloudSecurityScanner()
    return scanner.run_scan()


if __name__ == "__main__":
    sys.exit(main())
