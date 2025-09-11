# Home Assistant Recovery Automation Scripts

This folder contains automation scripts to help analyze and validate recovered Home Assistant files after SD card failure.

## Scripts Overview

### 1. `analyze_recovered_files.py` - File Discovery & Categorization
**Purpose:** Automatically scan PhotoRec recovery output to find Home Assistant configuration files

**Features:**
- Scans thousands of recovered files automatically
- Identifies HA config files by filename patterns and content
- Detects duplicates using file hashing
- Categorizes files (configuration, automations, scenes, secrets, etc.)
- Generates prioritized file lists for manual review
- Creates detailed analysis report

**Usage:**
```bash
# Use default samass recovery folder
python analyze_recovered_files.py

# Or specify custom folder
python analyze_recovered_files.py "C:\PhotoRec_Recovery\recup_dir.1"
```

**Default Recovery Folder:** `G:\My Drive\House Stuff\HomeAssistant\Corrupted image Sept 25\Recovery`

**Output:**
- `ha_recovery_report.md` - Detailed analysis report
- `ha_priority_files.txt` - Prioritized list of files to review

### 2. `validate_yaml_files.py` - YAML Validation & Quality Check
**Purpose:** Validate recovered YAML files for syntax errors and Home Assistant compatibility

**Features:**
- Validates YAML syntax of recovered files
- Identifies Home Assistant configuration sections
- Detects likely corrupted files
- Provides quality assessment and warnings
- Prioritizes files by usefulness for HA recovery

**Usage:**
```bash
python validate_yaml_files.py ha_priority_files.txt
```

**Output:**
- `ha_yaml_validation_report.md` - Validation results and recommendations

## Workflow

1. **Run PhotoRec** to recover files from failed SD card
2. **Run analyzer** to find HA files: `python analyze_recovered_files.py` (uses your default path)
3. **Run validator** to check quality: `python validate_yaml_files.py ha_priority_files.txt`
4. **Review reports** to identify best configuration files
5. **Set up new HA instance** with recovered configs

## Requirements

```bash
pip install pyyaml
```

## Expected Results

Based on 46k+ text files found at 10% scan completion, you should expect:
- Several hundred thousand recovered text files total
- Dozens to hundreds of Home Assistant configuration files
- Multiple versions of key files (configuration.yaml, automations.yaml, etc.)
- Some duplicate and corrupted files that need filtering

## File Patterns Detected

The scripts look for these HA file types:
- `configuration.yaml` - Main HA configuration
- `automations.yaml` - Automation rules  
- `scenes.yaml` - Scene definitions
- `secrets.yaml` - Passwords and tokens
- `groups.yaml` - Entity groupings
- `scripts.yaml` - Script definitions
- `customize.yaml` - Entity customizations
- `known_devices.yaml` - Device tracking
- Plus content-based detection for unnamed files

## Recovery Strategy

1. **Prioritize large, valid files** - More likely to be complete
2. **Check for duplicates** - Choose newest/largest version
3. **Validate before use** - Test with `hass --script check_config`
4. **Regenerate secrets** - Tokens may need to be recreated
5. **Test incrementally** - Add configurations gradually

Good luck with your recovery! These scripts should save you hours of manual file review.
