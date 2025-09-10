# Home Assistant SD Card Recovery - Complete Troubleshooting Log
**Date:** 2025-09-10
**Time Started:** ~09:00 UTC  
**Current Time:** 09:20 UTC
**User:** samass
**GitHub Profile:** https://github.com/samass
**Issue:** Failed Home Assistant SD card recovery after network connectivity loss

## Initial Problem Discovery
**Root Issue:** Home Assistant instance disappeared from router device list
- Home Assistant was no longer visible on network
- Device not showing up in router's connected devices
- Could not access Home Assistant web interface
- No response to ping attempts

**Initial Troubleshooting Steps:**
1. **Network Diagnostics:**
   - Checked router device list - HA missing
   - Attempted to ping Home Assistant IP - no response
   - Verified other network devices working normally
   - Ruled out network/router issues

2. **Hardware Investigation:**
   - Checked Home Assistant device power status
   - Attempted to access via direct connection
   - Led to physical SD card examination

## SD Card Physical Examination
**Discovery:** SD card showing critical failure symptoms
- Windows displaying multiple rapid autoplay notifications
- Read errors when attempting to access card contents
- Intermittent recognition/disconnection cycles
- Clear signs of hardware failure in progress

**Critical Decision Point:** 
- System was completely non-functional (not just network issue)
- SD card failure was root cause of network disappearance
- Immediate data recovery action required before total failure

## Hardware & Setup Context
- **Home Assistant:** Primary home automation system
- **Network Setup:** Static IP on home router
- **User Projects:** Active ESP32 development (samass/ESP32-Solar_PIR)
- **Development Environment:** PlatformIO for ESP32 projects
- **Related Repos:** 
  - samass/personal-finance-tool
  - samass/receipt-scanner  
  - samass/Car-Data-Display
- **Integration Complexity:** Likely extensive YAML configs for automations

## Recovery Strategy Decision
**Why Image First vs Direct Recovery:**
- ✅ SD card already showing read errors during initial access
- ✅ Multiple Windows autoplay notifications = unstable connection  
- ✅ Every read attempt stresses failing hardware further
- ✅ Direct recovery risks: card dying mid-process = total loss
- ✅ Imaging captures maximum recoverable data in current state
- ✅ Image allows unlimited recovery attempts without hardware stress
- ✅ **Network disappearance indicates system was already critically damaged**

## Step 1: Initial SD Card Imaging
**Tool Used:** HDD Raw Copy Tool
**Settings:** Compressed image output
**Reasoning:** Attempt to preserve space while capturing data
**Result:** Image created successfully despite read errors
**Lesson:** Always image failing storage first - hardware won't get better, only worse

## Step 2: First Recovery Attempt  
**Tool Used:** PhotoRec on compressed image
**Results:**
- Total files recovered: 5 text files
- File 1 (f0182528): 1KB, 120 characters of random numbers (corrupted)
- File 2: PlatformIO library text fragment ("his directory is intended for project specific libraries...")
  - *Note: Indicates ESP32 project data was present, correlating with samass/ESP32-Solar_PIR repo*
- Files 3-5: Corrupted with no useful information
- **No Home Assistant YAML configs found**

**Analysis:** Very poor recovery rate suggested compression interfering with file signature detection

## Step 3: Improved Imaging Strategy
**Decision:** Re-image with uncompressed output
**Reasoning:** 
- Compression artifacts may interfere with PhotoRec's file signature detection
- Raw sector data provides better recovery tool performance
- Worth the extra time/storage for critical configuration recovery
- **Network outage indicates configs are complex/valuable enough to warrant thorough recovery**

**Tool Used:** HDD Raw Copy Tool  
**Settings:** Uncompressed image output
**Result:** Successfully created larger, uncompressed image

## Step 4: Second Recovery Attempt
**Tool Used:** PhotoRec on uncompressed image
**Dramatic Improvement:**
- **2% scanned:** 826+ text files found (vs 5 total in compressed scan)
- **160x improvement** in file detection
- **Confirms:** Uncompressed imaging strategy was correct
- **Indicates:** Extensive configuration data likely recoverable

## Key Technical Lessons Learned

### 1. **Network Symptoms Can Indicate Storage Failure**
- Device disappearing from network = potential SD card corruption
- Complete system unresponsiveness often means storage failure
- Network troubleshooting should include storage health checks

### 2. **Always Image First Rule**
- Never attempt direct recovery on failing hardware
- Physical storage only degrades further with use
- One successful image > multiple failed direct attempts

### 3. **Compression Impact on Recovery**
- Compressed images can hide file signatures from recovery tools
- Raw, uncompressed images provide better recovery rates
- Storage space trade-off worth it for critical data

### 4. **Recovery Tool Behavior**
- PhotoRec works by scanning for file signatures (magic bytes)
- Different file types have different signature patterns
- YAML configs recovered as .txt files (text-based content)

### 5. **Early Warning Signs Recognition**
- Network disappearance = investigate hardware immediately
- Multiple autoplay notifications = hardware instability
- Read errors during normal access = immediate backup needed
- Don't wait for complete failure to start recovery process

## Home Assistant Specific Recovery Strategy

### Files to Look For:
```yaml
# Primary config files:
- configuration.yaml (main HA config)
- automations.yaml (automation rules)
- scenes.yaml (scene definitions)  
- secrets.yaml (passwords/tokens)
- groups.yaml (entity groupings)

# Secondary files:
- *.json files (device registrations, entity data)
- *.db files (history database)
- known_devices.yaml (device tracking)
- customize.yaml (entity customizations)

# Integration configs:
- Device-specific YAML files
- Custom component configurations
- Network/static IP settings
