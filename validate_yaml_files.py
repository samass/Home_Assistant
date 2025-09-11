#!/usr/bin/env python3
"""
Home Assistant YAML Validator
Validates recovered YAML files for syntax and HA compatibility
Created for samass HA recovery - 2025-09-10
"""

import yaml
import os
import sys
from pathlib import Path
import re

class HAYAMLValidator:
    def __init__(self):
        self.results = {
            'valid': [],
            'invalid': [],
            'warnings': [],
            'stats': {}
        }
        
        # Common HA configuration sections
        self.ha_sections = {
            'homeassistant', 'automation', 'script', 'scene', 'sensor',
            'binary_sensor', 'switch', 'light', 'climate', 'cover',
            'device_tracker', 'group', 'input_boolean', 'input_number',
            'input_select', 'input_text', 'timer', 'counter', 'zone'
        }
        
        # Patterns that might indicate corrupted content
        self.corruption_patterns = [
            re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\xFF]'),  # Non-printable chars
            re.compile(r'^[0-9\s]*$'),  # Only numbers and whitespace
            re.compile(r'^[^a-zA-Z]*$'),  # No letters at all
        ]

    def validate_file(self, file_path):
        """Validate a single YAML file"""
        result = {
            'file': str(file_path),
            'valid': False,
            'error': None,
            'warnings': [],
            'size': 0,
            'lines': 0,
            'ha_sections': [],
            'likely_corrupted': False
        }
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            result['size'] = len(content)
            result['lines'] = content.count('\n') + 1
            
            # Check for corruption patterns
            for pattern in self.corruption_patterns:
                if pattern.search(content):
                    result['likely_corrupted'] = True
                    result['warnings'].append("Contains suspicious patterns - may be corrupted")
                    break
            
            # Skip very small files
            if len(content.strip()) < 10:
                result['warnings'].append("File too small to be meaningful")
                return result
            
            # Try to parse YAML
            try:
                yaml_data = yaml.safe_load(content)
                result['valid'] = True
                
                # Check if it looks like HA config
                if isinstance(yaml_data, dict):
                    found_sections = []
                    for key in yaml_data.keys():
                        if isinstance(key, str) and key.lower() in self.ha_sections:
                            found_sections.append(key)
                    result['ha_sections'] = found_sections
                    
                    if not found_sections:
                        result['warnings'].append("No recognized HA sections found")
                
                elif isinstance(yaml_data, list):
                    # Check if it's a list of automations/scripts
                    if any(isinstance(item, dict) and 'alias' in item for item in yaml_data):
                        result['ha_sections'] = ['automation_list']
                    else:
                        result['warnings'].append("List format - check if valid HA structure")
                
            except yaml.YAMLError as e:
                result['error'] = f"YAML parsing error: {str(e)}"
                
                # Try to identify common issues
                if "found character" in str(e):
                    result['warnings'].append("Invalid characters - may be partially corrupted")
                elif "expected" in str(e):
                    result['warnings'].append("Syntax error - check indentation and structure")
            
        except Exception as e:
            result['error'] = f"File reading error: {str(e)}"
        
        return result

    def validate_files(self, file_paths):
        """Validate multiple files"""
        print(f"🔍 Validating {len(file_paths)} YAML files...")
        
        for i, file_path in enumerate(file_paths):
            if i % 50 == 0 and i > 0:
                print(f"   Processed {i}/{len(file_paths)} files...")
            
            result = self.validate_file(Path(file_path))
            
            if result['valid']:
                self.results['valid'].append(result)
            else:
                self.results['invalid'].append(result)
            
            if result['warnings']:
                self.results['warnings'].extend([
                    {'file': result['file'], 'warning': w} for w in result['warnings']
                ])
        
        print(f"✅ Validation complete!")

    def generate_report(self):
        """Generate validation report"""
        valid_count = len(self.results['valid'])
        invalid_count = len(self.results['invalid'])
        total_count = valid_count + invalid_count
        
        report = []
        report.append("# Home Assistant YAML Validation Report")
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"- Total files: {total_count}")
        report.append(f"- Valid YAML: {valid_count} ({valid_count/total_count*100:.1f}%)")
        report.append(f"- Invalid YAML: {invalid_count} ({invalid_count/total_count*100:.1f}%)")
        report.append(f"- Files with warnings: {len(self.results['warnings'])}")
        report.append("")
        
        # Valid files with HA sections
        ha_files = [f for f in self.results['valid'] if f['ha_sections']]
        report.append(f"## Valid Home Assistant Files ({len(ha_files)})")
        
        for file_info in sorted(ha_files, key=lambda x: len(x['ha_sections']), reverse=True):
            report.append(f"### {Path(file_info['file']).name}")
            report.append(f"- **Path:** `{file_info['file']}`")
            report.append(f"- **Size:** {file_info['size']} bytes ({file_info['lines']} lines)")
            report.append(f"- **HA Sections:** {', '.join(file_info['ha_sections'])}")
            if file_info['warnings']:
                report.append(f"- **Warnings:** {'; '.join(file_info['warnings'])}")
            report.append("")
        
        # Files needing attention
        problem_files = [f for f in self.results['valid'] if not f['ha_sections'] or f['warnings']]
        problem_files.extend(self.results['invalid'])
        
        if problem_files:
            report.append(f"## Files Needing Attention ({len(problem_files)})")
            
            for file_info in sorted(problem_files, key=lambda x: x['size'], reverse=True):
                report.append(f"### {Path(file_info['file']).name}")
                report.append(f"- **Path:** `{file_info['file']}`")
                report.append(f"- **Size:** {file_info['size']} bytes")
                report.append(f"- **Status:** {'Valid YAML' if file_info['valid'] else 'Invalid YAML'}")
                
                if file_info['error']:
                    report.append(f"- **Error:** {file_info['error']}")
                
                if file_info['warnings']:
                    report.append(f"- **Warnings:** {'; '.join(file_info['warnings'])}")
                
                if file_info['likely_corrupted']:
                    report.append(f"- **⚠️ LIKELY CORRUPTED - May not be recoverable**")
                
                report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("1. **Start with files that have HA sections** - most likely to be useful")
        report.append("2. **Large valid files** are more likely to contain complete configs")
        report.append("3. **Review warnings** - some files may be partially recoverable")
        report.append("4. **Skip corrupted files** unless they're the only copy available")
        report.append("5. **Test in HA check_config** before using in production")
        
        return "\n".join(report)

def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_yaml_files.py <file_list.txt>")
        print("Where file_list.txt contains one file path per line")
        sys.exit(1)
    
    file_list_path = sys.argv[1]
    
    if not os.path.exists(file_list_path):
        print(f"❌ File list not found: {file_list_path}")
        sys.exit(1)
    
    # Read file list
    with open(file_list_path, 'r') as f:
        file_paths = [line.strip() for line in f if line.strip()]
    
    # Filter for YAML files
    yaml_files = []
    for file_path in file_paths:
        # Remove priority prefix if present
        if ':' in file_path:
            file_path = file_path.split(':', 1)[1].strip()
        
        if file_path.lower().endswith(('.yaml', '.yml', '.txt')):
            if os.path.exists(file_path):
                yaml_files.append(file_path)
    
    if not yaml_files:
        print("❌ No YAML files found in the list")
        sys.exit(1)
    
    print("🏠 Home Assistant YAML Validator")
    print("=" * 50)
    
    validator = HAYAMLValidator()
    validator.validate_files(yaml_files)
    
    # Generate report
    report = validator.generate_report()
    
    # Save report
    report_file = "ha_yaml_validation_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📊 Validation complete!")
    print(f"📄 Report saved to: {report_file}")
    
    # Quick stats
    valid_ha_files = len([f for f in validator.results['valid'] if f['ha_sections']])
    print(f"\n🎯 Quick Summary:")
    print(f"   {valid_ha_files} files look like valid HA configurations")
    print(f"   {len(validator.results['valid'])} total valid YAML files")
    print(f"   {len(validator.results['invalid'])} files have YAML errors")

if __name__ == "__main__":
    main()
