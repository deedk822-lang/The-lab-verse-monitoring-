#!/usr/bin/env python3
"""
Script to interface with Alibaba Cloud Access Analyzer for security scanning
"""

import json
import subprocess
import sys
import tempfile
import os
from datetime import datetime


def run_alibaba_command(command):
    """Execute an Alibaba Cloud CLI command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error: {e.stderr}")
        return None


def get_access_analyzer_findings():
    """Get findings from Alibaba Cloud Access Analyzer"""
    findings = []

    # List all analyzers
    analyzers_output = run_alibaba_command("aliyun accessanalyzer ListAnalyzers --output json")

    if analyzers_output:
        try:
            analyzers = json.loads(analyzers_output)

            for analyzer in analyzers.get('analyzers', []):
                analyzer_name = analyzer['analyzerName']

                # Get findings for each analyzer
                findings_output = run_alibaba_command(
                    f"aliyun accessanalyzer ListFindings --analyzer-name {analyzer_name} --output json"
                )

                if findings_output:
                    analyzer_findings = json.loads(findings_output)

                    for finding in analyzer_findings.get('findings', []):
                        finding_detail = {
                            "id": finding.get('id'),
                            "resource": finding.get('resource'),
                            "status": finding.get('status'),
                            "severity": finding.get('severity'),
                            "principal": finding.get('principal', {}),
                            "condition": finding.get('condition', {}),
                            "createdAt": finding.get('createdAt')
                        }
                        findings.append(finding_detail)
        except json.JSONDecodeError:
            print("Failed to parse Access Analyzer output")

    return findings


def get_ecs_security_analysis():
    """Analyze ECS security configurations"""
    security_analysis = []

    # Get security groups
    sg_output = run_alibaba_command("aliyun ecs DescribeSecurityGroups --output json")

    if sg_output:
        try:
            sgs = json.loads(sg_output)

            for sg in sgs.get('SecurityGroups', {}).get('SecurityGroup', []):
                # Check for overly permissive rules
                permissions = sg.get('Permissions', {}).get('Permission', [])

                for perm in permissions:
                    port_range = perm.get('PortRange', '')
                    source_cidr = perm.get('SourceCidrIp', '')

                    # Flag overly permissive rules (e.g., 0.0.0.0/0 on all ports)
                    if source_cidr == '0.0.0.0/0' and port_range == '-1/-1':
                        security_analysis.append({
                            "type": "SECURITY_GROUP_ISSUE",
                            "resource": sg.get('SecurityGroupId'),
                            "issue": "Overly permissive rule allowing all traffic",
                            "details": f"Security group {sg.get('SecurityGroupName')} allows all IP addresses access to all ports"
                        })
        except json.JSONDecodeError:
            print("Failed to parse ECS security group output")

    return security_analysis


def generate_sarif_report(findings, ecs_analysis):
    """Generate SARIF format report for GitHub security scanning"""
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

    # Convert findings to SARIF format
    for finding in findings:
        result = {
            "ruleId": f"access-analyzer-{finding.get('severity', 'INFO').lower()}",
            "level": "warning" if finding.get('severity') in ['HIGH', 'CRITICAL'] else "note",
            "message": {
                "text": f"Access analyzer finding: {finding.get('id')} - Status: {finding.get('status')}"
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": finding.get('resource', 'unknown')
                        }
                    }
                }
            ],
            "properties": {
                "createdAt": finding.get('createdAt'),
                "principal": finding.get('principal', {}),
                "condition": finding.get('condition', {})
            }
        }
        sarif_report["runs"][0]["results"].append(result)

    # Add ECS security analysis results
    for issue in ecs_analysis:
        result = {
            "ruleId": f"{issue['type']}",
            "level": "error" if "ISSUE" in issue['type'] else "warning",
            "message": {
                "text": issue['issue']
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": issue['resource']
                        }
                    }
                }
            ],
            "properties": {
                "details": issue['details']
            }
        }
        sarif_report["runs"][0]["results"].append(result)

    return sarif_report


def main():
    print("Starting Alibaba Cloud Access Analyzer scan...")

    # Get access analyzer findings
    print("Getting access analyzer findings...")
    access_findings = get_access_analyzer_findings()

    # Get ECS security analysis
    print("Performing ECS security analysis...")
    ecs_analysis = get_ecs_security_analysis()

    # Generate SARIF report
    print("Generating SARIF report...")
    sarif_report = generate_sarif_report(access_findings, ecs_analysis)

    # Output the report
    output_file = "security-report.json"
    with open(output_file, 'w') as f:
        json.dump(sarif_report, f, indent=2)

    print(f"Security analysis completed. Report saved to {output_file}")

    # Print summary
    print(f"\nSummary:")
    print(f"- Access Analyzer Findings: {len(access_findings)}")
    print(f"- ECS Security Issues: {len(ecs_analysis)}")

    # Exit with error code if critical issues found
    critical_findings = [f for f in access_findings if f.get('severity') in ['CRITICAL', 'HIGH']]
    if critical_findings or ecs_analysis:
        print(f"- Critical/High findings detected: {len(critical_findings)}")
        print(f"- ECS security issues detected: {len(ecs_analysis)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
