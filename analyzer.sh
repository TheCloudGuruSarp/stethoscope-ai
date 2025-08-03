#!/bin/bash
# Stethoscope AI - Secure Snapshot Script v5.0
# This script is read-only and outputs Base64 encoded JSON.
# New Features: Security Scan, Package Update Check, Expanded Metrics, Locale Fix.

# Exit immediately if a command exits with a non-zero status.
set -e
set -o pipefail

# Force C locale for all commands to ensure consistent, non-localized output.
export LANG=C
export LC_ALL=C

# This function encodes the collected JSON data into Base64.
encode_and_output() {
    local data="$1"
    echo "$data" | base64 -w 0
}

# --- DATA COLLECTION FUNCTIONS ---

get_os_info() {
    printf '"os_info": {'
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        printf '"distro": "%s", "version": "%s",' "$NAME" "$VERSION_ID"
    else
        printf '"distro": "Unknown", "version": "Unknown",'
    fi
    printf '"kernel": "%s",' "$(uname -r)"
    printf '"hostname": "%s"' "$(hostname)"
    printf '},'
}

get_performance_info() {
    local cpu_idle=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    printf '"performance": {'
    printf '"load_average": "%s",' "$(cat /proc/loadavg | awk '{print $1, $2, $3}')"
    printf '"uptime_seconds": %s,' "$(cat /proc/uptime | awk '{print $1}')"
    printf '"running_processes": %s,' "$(ps -e --no-headers | wc -l)"
    printf '"cpu_usage_percent": %.1f' "$cpu_idle"
    printf '},'
}

get_memory_info() {
    local mem_info=$(</proc/meminfo)
    printf '"memory": {'
    printf '"total_kb": %s,' "$(echo "$mem_info" | grep MemTotal | awk '{print $2}')"
    printf '"available_kb": %s' "$(echo "$mem_info" | grep MemAvailable | awk '{print $2}')"
    printf '},'
}

get_disk_info() {
    printf '"disk_usage": ['
    df -P | grep '^/dev/' | while read -r line; do
        printf '{'
        printf '"filesystem": "%s",' "$(echo "$line" | awk '{print $1}')"
        printf '"use_percent": "%s",' "$(echo "$line" | awk '{print $5}')"
        printf '"mount_point": "%s"' "$(echo "$line" | awk '{print $6}')"
        printf '},'
    done | sed '$s/,$//'
    printf '],'
}

get_security_info() {
    printf '"security": {'
    local permit_root_login=$(grep -i "^PermitRootLogin" /etc/ssh/sshd_config | awk '{print $2}' || echo "not_set")
    local password_auth=$(grep -i "^PasswordAuthentication" /etc/ssh/sshd_config | awk '{print $2}' || echo "not_set")
    printf '"ssh_permit_root_login": "%s",' "$permit_root_login"
    printf '"ssh_password_auth": "%s",' "$password_auth"
    local fw_status="inactive"
    if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then fw_status="ufw_active"; fi
    if command -v firewall-cmd &> /dev/null && firewall-cmd --state | grep -q "running"; then fw_status="firewalld_active"; fi
    printf '"firewall_status": "%s"' "$fw_status"
    printf '},'
}

get_package_updates() {
    printf '"package_updates": "'
    local updates=""
    if command -v apt-get &> /dev/null; then
        updates=$(apt-get -s dist-upgrade | grep "^Inst" | awk '{print $2 " " $4}' | sed 's/[()]//g' | tr '\n' ';')
    elif command -v dnf &> /dev/null; then
        updates=$(dnf check-update --quiet | awk '{print $1 " " $2}' | tr '\n' ';')
    elif command -v yum &> /dev/null; then
        updates=$(yum check-update --quiet | awk '{print $1 " " $2}' | tr '\n' ';')
    fi
    printf '%s' "$updates"
    printf '",'
}

get_top_processes() {
    printf '"top_processes": ['
    ps_output=$( (ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu | head -n 6; ps -eo pid,user,%cpu,%mem,comm --sort=-%mem | head -n 6) | tail -n +2 | sort -u -k1,1n)
    first_line=true
    echo "$ps_output" | while read -r line; do
        if [ -z "$line" ]; then continue; fi
        if [ "$first_line" = false ]; then printf ','; fi
        first_line=false
        pid=$(echo "$line" | awk '{print $1}')
        user=$(echo "$line" | awk '{print $2}')
        cpu=$(echo "$line" | awk '{print $3}')
        mem=$(echo "$line" | awk '{print $4}')
        comm=$(echo "$line" | awk '{print $5}')
        printf '{"pid": %s, "user": "%s", "cpu_percent": %s, "mem_percent": %s, "command": "%s"}' "$pid" "$user" "$cpu" "$mem" "$comm"
    done
    printf ']'
}

main() {
    json_output=$(printf '{%s%s%s%s%s%s%s}' \
      "$(get_os_info)" \
      "$(get_performance_info)" \
      "$(get_memory_info)" \
      "$(get_disk_info)" \
      "$(get_security_info)" \
      "$(get_package_updates)" \
      "$(get_top_processes)" \
    )
    encode_and_output "$json_output"
}

main
