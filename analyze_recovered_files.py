#!/usr/bin/env python3
"""
Home Assistant Recovery File Analyzer
Automatically categorizes and analyzes recovered files from PhotoRec
Created for samass HA recovery - 2025-09-10
"""

import os
import re
import json
import yaml
from pathlib import Path
from collections import defaultdict, Counter
import hashlib

class HARecoveryAnalyzer:
    def __init__(self, recovery_folder):
        self.recovery_folder = Path(recovery_folder)
        self.results = {
            'ha_configs': [],
            'yaml_files': [],
            'json_files': [],
            'text_files': [],
            'automations': [],
            'scenes': [],
            'secrets': [],
            'duplicates': defaultdict(list),
            'large_files': [],
            'suspicious_files': []
        }
        
        # Home Assistant file patterns
        self.ha_patterns = {
            'configuration': re.compile(r'configuration\.ya?ml', re.IGNORECASE),
            'automations': re.compile(r'automations?\.ya?ml', re.IGNORECASE),
            'scenes': re.compile(r'scenes?\.ya?ml', re.IGNORECASE),
            'secrets': re.compile(r'secrets?\.ya?ml', re.IGNORECASE),
            'groups': re.compile(r'groups?\.ya?ml', re.IGNORECASE),
            'customize': re.compile(r'customize\.ya?ml', re.IGNORECASE),
            'known_devices': re.compile(r'known_devices\.ya?ml', re.IGNORECASE),
            'scripts': re.compile(r'scripts?\.ya?ml', re.IGNORECASE)
        }
        
        # HA content signatures
        self.ha_content_patterns = {
            'homeassistant': re.compile(r'homeassistant:', re.MULTILINE),
            'automation': re.compile(r'- alias:|trigger:|action:|condition:', re.MULTILINE),
            'sensor': re.compile(r'sensor:|platform:', re.MULTILINE),
            'switch': re.compile(r'switch:|platform:', re.MULTILINE),
            'light': re.compile(r'light:|platform:', re.MULTILINE),
            'device_tracker': re.compile(r'device_tracker:', re.MULTILINE),
            'esp_device': re.compile(r'esphome|esp32|esp8266', re.IGNORECASE),
            'integration': re.compile(r'integration:|component:', re.MULTILINE)
        }

    def get_file_hash(self, file_path):
        """Generate MD5 hash for duplicate detection"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return None

    def is_likely_ha_file(self, file_path):
        """Check if file is likely a Home Assistant configuration"""
        try:
            # Check filename patterns first
            filename = file_path.name.lower()
            for pattern_name, pattern in self.ha_patterns.items():
                if pattern.search(filename):
                    return True, f"filename_match_{pattern_name}"
            
            # Check file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2048)  # Read first 2KB for performance
                
                for pattern_name, pattern in self.ha_content_patterns.items():
                    if pattern.search(content):
                        return True, f"content_match_{pattern_name}"
                        
            return False, "no_match"
        except:
            return False, "read_error"

    def analyze_yaml_file(self, file_path):
        """Analyze YAML file structure"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Try to parse as YAML
            try:
                yaml_data = yaml.safe_load(content)
                return {
                    'valid_yaml': True,
                    'structure': type(yaml_data).__name__,
                    'keys': list(yaml_data.keys()) if isinstance(yaml_data, dict) else None,
                    'size': len(content)
                }
            except:
                return {
                    'valid_yaml': False,
                    'size': len(content),
                    'lines': content.count('\n')
                }
        except:
            return {'error': 'read_failed'}

    def scan_files(self):
        """Main scanning function"""
        print(f"🔍 Scanning {self.recovery_folder} and all subfolders for Home Assistant files...")
        print(f"📁 Recovery path: {self.recovery_folder}")
        
        # Check if subfolders exist and report structure
        subfolders = [d for d in self.recovery_folder.iterdir() if d.is_dir()]
        if subfolders:
            print(f"📂 Found {len(subfolders)} subfolders to scan:")
            for subfolder in sorted(subfolders)[:5]:  # Show first 5
                print(f"   - {subfolder.name}")
            if len(subfolders) > 5:
                print(f"   ... and {len(subfolders) - 5} more folders")
        
        file_count = 0
        ha_count = 0
        
        # Get all text files recursively
        text_extensions = {'.txt', '.yaml', '.yml', '.json', '.conf', '.cfg', '.py'}
        
        print(f"🔄 Starting recursive scan...")
        for file_path in self.recovery_folder.rglob('*'):
            if not file_path.is_file():
                continue
                
            file_count += 1
            if file_count % 5000 == 0:
                print(f"   📊 Processed {file_count} files, found {ha_count} HA-related files...")
            
            # Skip very large files initially
            try:
                file_size = file_path.stat().st_size
                if file_size > 10 * 1024 * 1024:  # 10MB
                    self.results['large_files'].append({
                        'path': str(file_path),
                        'size': file_size
                    })
                    continue
            except:
                continue
            
            # Check if it's a text file
            if file_path.suffix.lower() in text_extensions or file_path.suffix == '':
                is_ha, match_type = self.is_likely_ha_file(file_path)
                
                if is_ha:
                    ha_count += 1
                    file_info = {
                        'path': str(file_path),
                        'name': file_path.name,
                        'size': file_size,
                        'match_type': match_type,
                        'hash': self.get_file_hash(file_path),
                        'subfolder': file_path.parent.name  # Track which subfolder
                    }
                    
                    # Categorize by type
                    if 'configuration' in match_type:
                        self.results['ha_configs'].append(file_info)
                    elif 'automation' in match_type:
                        self.results['automations'].append(file_info)
                    elif 'scene' in match_type:
                        self.results['scenes'].append(file_info)
                    elif 'secret' in match_type:
                        self.results['secrets'].append(file_info)
                    else:
                        self.results['yaml_files'].append(file_info)
                    
                    # Check for duplicates
                    if file_info['hash']:
                        self.results['duplicates'][file_info['hash']].append(file_info)
                
                elif file_path.suffix.lower() == '.json':
                    self.results['json_files'].append({
                        'path': str(file_path),
                        'name': file_path.name,
                        'size': file_size,
                        'subfolder': file_path.parent.name
                    })
        
        print(f"✅ Scan complete! Processed {file_count} files, found {ha_count} HA-related files")
        print(f"📈 Success rate: {ha_count/file_count*100:.3f}% of files were HA-related")

    def generate_report(self):
        """Generate detailed analysis report"""
        report = []
        report.append("# Home Assistant Recovery Analysis Report")
        report.append(f"Generated: {os.getcwd()}")
        report.append(f"Scanned folder: {self.recovery_folder}")
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"- Configuration files: {len(self.results['ha_configs'])}")
        report.append(f"- Automation files: {len(self.results['automations'])}")
        report.append(f"- Scene files: {len(self.results['scenes'])}")
        report.append(f"- Secret files: {len(self.results['secrets'])}")
        report.append(f"- Other YAML files: {len(self.results['yaml_files'])}")
        report.append(f"- JSON files: {len(self.results['json_files'])}")
        report.append(f"- Large files (>10MB): {len(self.results['large_files'])}")
        report.append("")
        
        # Duplicates
        duplicates = {k: v for k, v in self.results['duplicates'].items() if len(v) > 1}
        report.append(f"## Duplicate Files ({len(duplicates)} sets)")
        for file_hash, files in duplicates.items():
            report.append(f"### Hash: {file_hash[:8]}...")
            for file_info in files:
                report.append(f"- {file_info['path']} ({file_info['size']} bytes)")
            report.append("")
        
        # Key files found
        report.append("## Key Home Assistant Files")
        
        if self.results['ha_configs']:
            report.append("### Configuration Files")
            for file_info in sorted(self.results['ha_configs'], key=lambda x: x['size'], reverse=True):
                report.append(f"- **{file_info['name']}** ({file_info['size']} bytes)")
                report.append(f"  Path: `{file_info['path']}`")
                report.append(f"  Subfolder: {file_info['subfolder']}")
                report.append(f"  Match: {file_info['match_type']}")
            report.append("")
        
        if self.results['automations']:
            report.append("### Automation Files")
            for file_info in sorted(self.results['automations'], key=lambda x: x['size'], reverse=True):
                report.append(f"- **{file_info['name']}** ({file_info['size']} bytes)")
                report.append(f"  Path: `{file_info['path']}`")
                report.append(f"  Subfolder: {file_info['subfolder']}")
            report.append("")
        
        # Recommendations
        report.append("## Recovery Recommendations")
        report.append("1. **Start with largest configuration files** - likely most complete")
        report.append("2. **Check duplicates** - choose newest/largest version")
        report.append("3. **Validate YAML syntax** before using")
        report.append("4. **Review secrets files** - may need to regenerate tokens")
        report.append("5. **Test automations** individually before bulk import")
        
        return "\n".join(report)

    def save_file_list(self, filename):
        """Save prioritized file list for manual review"""
        priority_files = []
        
        # Add configuration files (highest priority)
        for file_info in sorted(self.results['ha_configs'], key=lambda x: x['size'], reverse=True):
            priority_files.append(f"HIGH_PRIORITY: {file_info['path']}")
        
        # Add automations
        for file_info in sorted(self.results['automations'], key=lambda x: x['size'], reverse=True):
            priority_files.append(f"AUTOMATION: {file_info['path']}")
        
        # Add secrets
        for file_info in sorted(self.results['secrets'], key=lambda x: x['size'], reverse=True):
            priority_files.append(f"SECRETS: {file_info['path']}")
        
        # Add other YAML files
        for file_info in sorted(self.results['yaml_files'], key=lambda x: x['size'], reverse=True):
            priority_files.append(f"YAML: {file_info['path']}")
        
        with open(filename, 'w') as f:
            f.write("\n".join(priority_files))
        
        print(f"📝 Priority file list saved to: {filename}")

def main():
    import sys
    
    # Default to samass's recovery folder if no argument provided
    default_recovery_folder = r"G:\My Drive\House Stuff\HomeAssistant\Corrupted image Sept 25\Recovery"
    
    if len(sys.argv) == 1:
        recovery_folder = default_recovery_folder
        print(f"Using default recovery folder: {recovery_folder}")
    elif len(sys.argv) == 2:
        recovery_folder = sys.argv[1]
    else:
        print("Usage: python analyze_recovered_files.py [recovery_folder]")
        print(f"Default: python analyze_recovered_files.py")
        print(f"Custom:  python analyze_recovered_files.py 'C:\\PhotoRec_Recovery\\recup_dir.1'")
        sys.exit(1)
    
    if not os.path.exists(recovery_folder):
        print(f"❌ Recovery folder not found: {recovery_folder}")
        print(f"Please check the path exists and try again.")
        sys.exit(1)
    
    print("🏠 Home Assistant Recovery File Analyzer")
    print("=" * 50)
    
    analyzer = HARecoveryAnalyzer(recovery_folder)
    analyzer.scan_files()
    
    # Generate report
    report = analyzer.generate_report()
    
    # Save files
    report_file = "ha_recovery_report.md"
    priority_file = "ha_priority_files.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    analyzer.save_file_list(priority_file)
    
    print(f"📊 Analysis complete!")
    print(f"📄 Report saved to: {report_file}")
    print(f"📋 Priority files saved to: {priority_file}")
    print("\n" + "="*50)
    print("NEXT STEPS:")
    print("1. Review the generated report")
    print("2. Check priority files list for key configurations")
    print("3. Validate YAML syntax of recovered files")
    print("4. Set up new HA instance and import configs")

if __name__ == "__main__":
    main()
