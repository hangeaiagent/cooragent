#!/bin/bash
# Universal Daily Security Monitoring Script (Optimized Version)
# Purpose: Automated daily security check and threat detection for any server
# Schedule: Daily at 5:00 AM
# Compatible: CentOS/RHEL/Ubuntu servers with system mail
# Version: 3.0 - Only send emails when threats are detected

# Email configuration
EMAIL="402493977@qq.com"
FROM_EMAIL="402493977@qq.com"

# Auto-detect server information
get_server_info() {
    # Get server IP address - try multiple methods
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || curl -s ipecho.net/plain 2>/dev/null || hostname -I | awk '{print $1}' || echo "Unknown")
    
    # Get hostname
    SERVER_HOSTNAME=$(hostname)
    
    # Get OS info
    if [ -f /etc/os-release ]; then
        OS_INFO=$(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)
    else
        OS_INFO=$(uname -s)
    fi
}

# Send security notification email function (using system mail) - ONLY FOR THREATS
send_threat_email() {
    local subject=$1
    local body=$2
    
    # Get current server info
    get_server_info
    
    # Construct email content
    email_content="🚨 SECURITY ALERT - THREATS DETECTED 🚨
==========================================
Server Information:
==================
Hostname: $SERVER_HOSTNAME
Public IP: $SERVER_IP
OS: $OS_INFO
Alert Time: $(date)
Alert Type: Threat Detection
========================================

$body

========================================
This email is automatically sent by Universal Security Monitoring System
Server: $SERVER_HOSTNAME ($SERVER_IP)
Monitoring Script: $(basename $0)
Script Location: $(pwd)/$(basename $0)

⚠️ IMPORTANT: This email is only sent when actual threats are detected.
Please take immediate action to investigate and remediate."

    # Send email using system mail command
    if command -v mail >/dev/null 2>&1; then
        echo "$email_content" | mail -s "🚨 [$SERVER_HOSTNAME] $subject" "$EMAIL"
        echo "📧 THREAT ALERT email sent to $EMAIL"
        echo "   Server: $SERVER_HOSTNAME ($SERVER_IP)"
        echo "   Subject: 🚨 [$SERVER_HOSTNAME] $subject"
    else
        echo "⚠️  mail command not available, threat alert saved to log"
        echo "📝 Threat alert content saved to log file"
        echo "Subject: 🚨 [$SERVER_HOSTNAME] $subject" >> "$DAILY_LOG"
        echo "$email_content" >> "$DAILY_LOG"
        echo "========================" >> "$DAILY_LOG"
    fi
}

echo "🔍 Starting Daily Security Check..."
echo "Time: $(date)"

# Get server information
get_server_info
echo "Server: $SERVER_HOSTNAME ($SERVER_IP)"
echo "========================================"

# Set variables
DAILY_LOG="/var/log/daily_security_check.log"
UPLOAD_DIR1="/alidata/server/tomcat/webapps/myhub/upload"
UPLOAD_DIR2="/alidata/server/tomcat8081/webapps/myhub/upload"
TEMP_REPORT="/tmp/daily_security_report_$(date +%Y%m%d).txt"

# Create daily log entry
echo "$(date): Daily security check started on $SERVER_HOSTNAME ($SERVER_IP)" | tee -a "$DAILY_LOG"

# Initialize threat detection variables
THREATS_FOUND=0
CRITICAL_THREATS=0
REPORT_CONTENT=""
THREAT_DETAILS=""

# Check for suspicious files
echo "🔍 Scanning for suspicious files..."

# Check tomcat directory
if [ -d "$UPLOAD_DIR1" ]; then
    echo "Checking tomcat upload directory: $UPLOAD_DIR1"
    SUSPICIOUS_FILES=$(find "$UPLOAD_DIR1" -name "*.jsp" -o -name "*.php" -o -name "*.tmp" -o -name "*.sh" 2>/dev/null | grep -v ".htaccess")
    if [ ! -z "$SUSPICIOUS_FILES" ]; then
        THREATS_FOUND=$((THREATS_FOUND + 1))
        CRITICAL_THREATS=$((CRITICAL_THREATS + 1))
        echo "⚠️  Suspicious files found in tomcat directory:"
        echo "$SUSPICIOUS_FILES"
        REPORT_CONTENT="$REPORT_CONTENT\n⚠️  TOMCAT DIRECTORY THREATS:\n$SUSPICIOUS_FILES\n"
        
        # Build detailed threat information
        THREAT_DETAILS="$THREAT_DETAILS

🚨 TOMCAT DIRECTORY THREATS DETECTED:
=====================================
Location: $UPLOAD_DIR1
Files Found:
$SUSPICIOUS_FILES

File Analysis:
==============
$(echo "$SUSPICIOUS_FILES" | while read file; do
    if [ -f "$file" ]; then
        echo "File: $file"
        echo "Size: $(stat -c%s "$file" 2>/dev/null || echo "Unknown") bytes"
        echo "Modified: $(stat -c%y "$file" 2>/dev/null || echo "Unknown")"
        echo "MD5: $(md5sum "$file" 2>/dev/null | cut -d' ' -f1 || echo "Unable to calculate")"
        echo "---"
    fi
done)"
    fi
else
    echo "⚠️  Tomcat upload directory not found: $UPLOAD_DIR1"
    REPORT_CONTENT="$REPORT_CONTENT\n⚠️  TOMCAT DIRECTORY: NOT FOUND ($UPLOAD_DIR1)\n"
fi

# Check tomcat8081 directory
if [ -d "$UPLOAD_DIR2" ]; then
    echo "Checking tomcat8081 upload directory: $UPLOAD_DIR2"
    SUSPICIOUS_FILES=$(find "$UPLOAD_DIR2" -name "*.jsp" -o -name "*.php" -o -name "*.tmp" -o -name "*.sh" 2>/dev/null | grep -v ".htaccess")
    if [ ! -z "$SUSPICIOUS_FILES" ]; then
        THREATS_FOUND=$((THREATS_FOUND + 1))
        CRITICAL_THREATS=$((CRITICAL_THREATS + 1))
        echo "⚠️  Suspicious files found in tomcat8081 directory:"
        echo "$SUSPICIOUS_FILES"
        REPORT_CONTENT="$REPORT_CONTENT\n⚠️  TOMCAT8081 DIRECTORY THREATS:\n$SUSPICIOUS_FILES\n"
        
        # Add to threat details
        THREAT_DETAILS="$THREAT_DETAILS

🚨 TOMCAT8081 DIRECTORY THREATS DETECTED:
=========================================
Location: $UPLOAD_DIR2
Files Found:
$SUSPICIOUS_FILES

File Analysis:
==============
$(echo "$SUSPICIOUS_FILES" | while read file; do
    if [ -f "$file" ]; then
        echo "File: $file"
        echo "Size: $(stat -c%s "$file" 2>/dev/null || echo "Unknown") bytes"
        echo "Modified: $(stat -c%y "$file" 2>/dev/null || echo "Unknown")"
        echo "MD5: $(md5sum "$file" 2>/dev/null | cut -d' ' -f1 || echo "Unable to calculate")"
        echo "---"
    fi
done)"
    fi
else
    echo "⚠️  Tomcat8081 upload directory not found: $UPLOAD_DIR2"
    REPORT_CONTENT="$REPORT_CONTENT\n⚠️  TOMCAT8081 DIRECTORY: NOT FOUND ($UPLOAD_DIR2)\n"
fi

# Check security configurations
echo "🔧 Verifying security configurations..."

# Check .htaccess files
HTACCESS_STATUS=""
MISSING_HTACCESS=0
for UPLOAD_DIR in "$UPLOAD_DIR1" "$UPLOAD_DIR2"; do
    if [ -f "$UPLOAD_DIR/.htaccess" ]; then
        HTACCESS_STATUS="$HTACCESS_STATUS\n✅ $UPLOAD_DIR/.htaccess - Present"
        echo "✅ Found .htaccess: $UPLOAD_DIR/.htaccess"
    else
        HTACCESS_STATUS="$HTACCESS_STATUS\n❌ $UPLOAD_DIR/.htaccess - Missing"
        echo "❌ Missing .htaccess: $UPLOAD_DIR/.htaccess"
        THREATS_FOUND=$((THREATS_FOUND + 1))
        MISSING_HTACCESS=$((MISSING_HTACCESS + 1))
    fi
done

# Add missing .htaccess to threat details if any
if [ $MISSING_HTACCESS -gt 0 ]; then
    THREAT_DETAILS="$THREAT_DETAILS

🚨 SECURITY CONFIGURATION ISSUES:
==================================
Missing .htaccess files detected:
$HTACCESS_STATUS

Impact: Upload directories are not properly protected against script execution.
Risk Level: HIGH - Web shells could be executed if uploaded."
fi

# Check system security status
echo "🛡️ Checking system security status..."

# Check YunJing status (Tencent Cloud Security)
YUNJING_STATUS="❌ Not Running"
if pgrep -f "YunJing" > /dev/null 2>&1; then
    YUNJING_STATUS="✅ Running"
    echo "✅ YunJing Security: Running"
else
    echo "❌ YunJing Security: Not Running"
    THREATS_FOUND=$((THREATS_FOUND + 1))
    THREAT_DETAILS="$THREAT_DETAILS

🚨 SECURITY SOFTWARE ISSUE:
============================
YunJing Security: Not Running
Impact: Host intrusion detection system is offline.
Risk Level: MEDIUM - Reduced threat detection capability."
fi

# Check for recent security events
RECENT_EVENTS=$(grep -c "$(date +%Y-%m-%d)" /var/log/emergency_response.log 2>/dev/null || echo "0")

# Check system load and basic health
SYSTEM_LOAD=$(uptime | awk -F'load average:' '{print $2}' | sed 's/^[ \t]*//')
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.2f%%", $3*100/$2}')

# Generate daily report
cat > "$TEMP_REPORT" << EOF
Daily Security Check Report
===========================
Date: $(date)
Server: $SERVER_HOSTNAME
Public IP: $SERVER_IP
Operating System: $OS_INFO

Threat Detection Summary:
========================
🎯 Threats Found: $THREATS_FOUND
🚨 Critical Threats: $CRITICAL_THREATS
📂 Directories Checked: 2
🔍 File Types Scanned: JSP, PHP, TMP, SH
📋 Scan Locations:
   - $UPLOAD_DIR1
   - $UPLOAD_DIR2

Security Configuration Status:
==============================
$HTACCESS_STATUS

System Security Status:
=======================
🛡️ YunJing Security: $YUNJING_STATUS
📊 Recent Security Events: $RECENT_EVENTS
🔍 Last Emergency Response: $(ls -t /var/log/emergency_response.log 2>/dev/null | head -1 | xargs stat -c %y 2>/dev/null || echo "No recent activity")

System Health Status:
=====================
💻 System Load: $SYSTEM_LOAD
💾 Disk Usage: $DISK_USAGE%
🧠 Memory Usage: $MEMORY_USAGE
⏰ Uptime: $(uptime | awk -F'up ' '{print $2}' | awk -F',' '{print $1}')

Detailed Findings:
==================
$REPORT_CONTENT

Email Notification Policy:
==========================
📧 Threat Alert: $(if [ $THREATS_FOUND -gt 0 ]; then echo "SENT - Threats detected"; else echo "NOT SENT - No threats found"; fi)
📧 Routine Report: NOT SENT - Email only sent when threats detected
📧 Start Notification: NOT SENT - Reduced email frequency

Recommendations:
================
- Review any detected suspicious files immediately
- Ensure .htaccess security rules are in place for all upload directories
- Monitor upload activities and access logs regularly
- Keep security software (YunJing) updated and running
- Consider implementing file integrity monitoring (AIDE/Tripwire)
- Regular security patches and system updates
- Monitor system resources for anomalies

Next Scheduled Check: $(date -d "tomorrow 5:00" "+%Y-%m-%d 05:00")
Check Frequency: Daily at 05:00 (Local Time)
Report Location: $TEMP_REPORT
Log File: $DAILY_LOG
EOF

# Log completion
echo "$(date): Daily security check completed on $SERVER_HOSTNAME ($SERVER_IP) - $THREATS_FOUND threats found" | tee -a "$DAILY_LOG"

# Send threat notification ONLY if threats are detected
if [ $THREATS_FOUND -gt 0 ]; then
    echo "🚨 THREATS DETECTED - Sending alert email..."
    
    # Send high priority notification for threats
    send_threat_email "🚨 SECURITY THREATS DETECTED - Immediate Action Required" "Multiple security threats detected during daily security check on $SERVER_HOSTNAME!

📊 THREAT SUMMARY:
==================
🎯 Total Threats: $THREATS_FOUND
🚨 Critical Threats: $CRITICAL_THREATS
⏰ Detection Time: $(date)
🖥️  Server: $SERVER_HOSTNAME ($SERVER_IP)
📋 Full Report: $TEMP_REPORT

$THREAT_DETAILS

🚨 IMMEDIATE ACTION REQUIRED:
=============================
Please review the detected threats and take appropriate action on server $SERVER_HOSTNAME.

Emergency Response Options:
==========================
1. Run emergency threat response script:
   /opt/emergency_threat_response.sh

2. Manual investigation:
   - Check web server logs: /var/log/httpd/ or /var/log/nginx/
   - Review upload directories for suspicious activity
   - Verify file permissions and ownership

3. Contact system administrator immediately

RECOMMENDED NEXT STEPS:
=======================
1. Isolate suspicious files immediately
2. Review web server access logs
3. Check for unauthorized access attempts
4. Verify integrity of web applications
5. Update security configurations
6. Run comprehensive malware scan

Server Details for Reference:
============================
Hostname: $SERVER_HOSTNAME
IP Address: $SERVER_IP
OS: $OS_INFO
Report Time: $(date)
Report File: $TEMP_REPORT

$(cat "$TEMP_REPORT")"

    echo "📧 Threat alert email sent to $EMAIL"
else
    echo "✅ NO THREATS DETECTED - No email notification sent"
    echo "📝 All clear - security check completed successfully"
    echo "📊 Summary: 0 threats found, system secure"
fi

echo ""
echo "📊 Daily security check summary:"
echo "- Server: $SERVER_HOSTNAME ($SERVER_IP)"
echo "- Threats found: $THREATS_FOUND"
echo "- Critical threats: $CRITICAL_THREATS"
echo "- Report saved: $TEMP_REPORT"
echo "- Log file: $DAILY_LOG"
echo "- Email sent: $(if [ $THREATS_FOUND -gt 0 ]; then echo "YES (Threat Alert)"; else echo "NO (All Clear)"; fi)"
echo ""
echo "🔍 View full report: cat $TEMP_REPORT"
echo "📋 View log file: tail -f $DAILY_LOG"
echo "========================================"