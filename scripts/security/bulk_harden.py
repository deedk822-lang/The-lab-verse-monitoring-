#!/usr/bin/env python3
"""
Bulk Security Hardening Script
Walks repository tree and hardens all critical files using Moonshot AI
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import the core hardener
from secure_file import MoonshotSecurityHardener


class BulkSecurityHardener:
    """Bulk harden multiple files in a repository"""
    
    # File patterns to harden
    CRITICAL_PATTERNS = [
        "*.py",
        "*.yml",
        "*.yaml",
        "Dockerfile*",
        "*.env.example",
        "*.sh",
        "*.bash",
        "*.js",
        "*.ts",
        "*.go",
        "*.conf",
        "*.config"
    ]
    
    # Directories to exclude
    EXCLUDE_DIRS = {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        "dist",
        "build",
        ".pytest_cache",
        ".mypy_cache",
        "coverage",
        ".next",
        "target"
    }
    
    # Files to exclude
    EXCLUDE_FILES = {
        ".env",  # Don't touch actual .env files with real secrets
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "go.sum",
        "Pipfile.lock"
    }
    
    def __init__(self, repo_path: str, output_dir: Optional[str] = None, 
                 max_workers: int = 4, dry_run: bool = False):
        self.repo_path = Path(repo_path).resolve()
        self.output_dir = Path(output_dir).resolve() if output_dir else None
        self.max_workers = max_workers
        self.dry_run = dry_run
        self.hardener = MoonshotSecurityHardener()
        
    def find_files_to_harden(self) -> List[Path]:
        """Find all files matching critical patterns"""
        
        files_to_harden = []
        
        for pattern in self.CRITICAL_PATTERNS:
            for file_path in self.repo_path.rglob(pattern):
                # Skip if in excluded directory
                if any(excluded in file_path.parts for excluded in self.EXCLUDE_DIRS):
                    continue
                
                # Skip if excluded file
                if file_path.name in self.EXCLUDE_FILES:
                    continue
                
                # Skip if not a file
                if not file_path.is_file():
                    continue
                
                files_to_harden.append(file_path)
        
        # Remove duplicates and sort
        files_to_harden = sorted(set(files_to_harden))
        
        return files_to_harden
    
    def harden_file_wrapper(self, file_path: Path) -> Dict[str, Any]:
        """Wrapper for hardening a single file with proper path handling"""
        
        if self.dry_run:
            print(f"[DRY RUN] Would harden: {file_path}")
            return {
                "status": "dry_run",
                "original_path": str(file_path),
                "output_path": str(file_path)
            }
        
        # Determine output path
        if self.output_dir:
            # Preserve directory structure in output
            rel_path = file_path.relative_to(self.repo_path)
            output_path = self.output_dir / rel_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Overwrite original
            output_path = file_path
        
        # Harden the file
        result = self.hardener.harden_file(str(file_path), str(output_path))
        
        return result
    
    def harden_all(self) -> Dict[str, Any]:
        """Harden all critical files in the repository"""
        
        print(f"🔍 Scanning repository: {self.repo_path}")
        
        files = self.find_files_to_harden()
        
        print(f"📋 Found {len(files)} files to harden")
        
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No files will be modified\n")
        
        results = {
            "total_files": len(files),
            "success": 0,
            "failed": 0,
            "errors": [],
            "files": []
        }
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.harden_file_wrapper, file_path): file_path
                for file_path in files
            }
            
            # Collect results
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                
                try:
                    result = future.result()
                    results["files"].append(result)
                    
                    if result["status"] == "success" or result["status"] == "dry_run":
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                        if "error" in result:
                            results["errors"].append({
                                "file": str(file_path),
                                "error": result["error"]
                            })
                
                except Exception as e:
                    results["failed"] += 1
                    error_info = {
                        "file": str(file_path),
                        "error": str(e)
                    }
                    results["errors"].append(error_info)
                    print(f"❌ Failed to process {file_path}: {e}", file=sys.stderr)
        
        return results


def main():
    """CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="Bulk security hardening using Moonshot AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Harden all files in current directory (overwrites originals)
  python bulk_harden.py .
  
  # Harden and save to separate directory
  python bulk_harden.py . --output ./hardened
  
  # Dry run to see what would be hardened
  python bulk_harden.py . --dry-run
  
  # Use more parallel workers
  python bulk_harden.py . --workers 8
        """
    )
    
    parser.add_argument(
        "repo_path",
        help="Path to repository to harden"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output directory (preserves structure). If not set, overwrites originals."
    )
    
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Dry run - don't actually modify files"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    # Validate repo path
    if not os.path.exists(args.repo_path):
        print(f"❌ Repository path not found: {args.repo_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Create bulk hardener
        bulk_hardener = BulkSecurityHardener(
            repo_path=args.repo_path,
            output_dir=args.output,
            max_workers=args.workers,
            dry_run=args.dry_run
        )
        
        # Run bulk hardening
        results = bulk_hardener.harden_all()
        
        # Output results
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("\n" + "="*60)
            print("📊 BULK HARDENING RESULTS")
            print("="*60)
            print(f"Total files:     {results['total_files']}")
            print(f"✅ Success:      {results['success']}")
            print(f"❌ Failed:       {results['failed']}")
            
            if results['errors']:
                print("\n⚠️  ERRORS:")
                for error in results['errors']:
                    print(f"  • {error['file']}: {error['error']}")
            
            print("="*60)
        
        # Exit with appropriate code
        sys.exit(0 if results['failed'] == 0 else 1)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

