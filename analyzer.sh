#!/bin/bash
# Stethoscope AI - Secure Snapshot Script v4.0
# This script is read-only and outputs Base64 encoded JSON.
# New Feature: Added security configuration checks.

# Exit immediately if a command exits with a non-zero status.
set -e
set -o pipefail

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
        printf '"distro": "%s", "version": "%s"' "$NAME" "$VERSION_ID"
    else
        printf '"distro": "Unknown", "version": "Unknown"'
    fi
    printf '},'
}

get_hardware_info() {
    printf '"hardware": {'
    printf '"cpu_model": "%s",' "$(grep "model name" /proc/cpuinfo | head -n 1 | cut -d: -f2 | sed 's/^[ \t]*//')"
    printf '"cpu_cores": %s,' "$(grep -c ^processor /proc/cpuinfo)"
    printf '"ram_total_kb": %s' "$(grep MemTotal /proc/meminfo | awk '{print $2}')"
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
    printf '"free_kb": %s,' "$(echo "$mem_info" | grep MemFree | awk '{print $2}')"
    printf '"available_kb": %s,' "$(echo "$mem_info" | grep MemAvailable | awk '{print $2}')"
    printf '"buffers_kb": %s,' "$(echo "$mem_info" | grep Buffers | awk '{print $2}')"
    printf '"cached_kb": %s' "$(echo "$mem_info" | grep "^Cached" | awk '{print $2}')"
    printf '},'
}

get_disk_info() {
    printf '"disk_usage": ['
    df -P | grep '^/dev/' | while read -r line; do
        printf '{'
        printf '"filesystem": "%s",' "$(echo "$line" | awk '{print $1}')"
        printf '"size": "%s",' "$(echo "$line" | awk '{print $2}')"
        printf '"used": "%s",' "$(echo "$line" | awk '{print $3}')"
        printf '"available": "%s",' "$(echo "$line" | awk '{print $4}')"
        printf '"use_percent": "%s",' "$(echo "$line" | awk '{print $5}')"
        printf '"mount_point": "%s"' "$(echo "$line" | awk '{print $6}')"
        printf '},'
    done | sed '$s/,$//'
    printf '],'
}

# --- NEW SECURITY FUNCTION ---
get_security_info() {
    printf '"security": {'
    # SSH Configuration
    local permit_root_login=$(grep -i "^PermitRootLogin" /etc/ssh/sshd_config | awk '{print $2}' || echo "not_set")
    local password_auth=$(grep -i "^PasswordAuthentication" /etc/ssh/sshd_config | awk '{print $2}' || echo "not_set")
    printf '"ssh_permit_root_login": "%s",' "$permit_root_login"
    printf '"ssh_password_auth": "%s",' "$password_auth"

    # Firewall Status
    local fw_status="inactive"
    if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        fw_status="ufw_active"
    elif command -v firewall-cmd &> /dev/null && firewall-cmd --state | grep -q "running"; then
        fw_status="firewalld_active"
    fi
    printf '"firewall_status": "%s"' "$fw_status"
    printf '},'
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

# --- MAIN FUNCTION ---
main() {
    json_output=$(printf '{%s%s%s%s%s%s%s}' \
      "$(get_os_info)" \
      "$(get_hardware_info)" \
      "$(get_performance_info)" \
      "$(get_memory_info)" \
      "$(get_disk_info)" \
      "$(get_security_info)" \
      "$(get_top_processes)" \
    )
    encode_and_output "$json_output"
}

main
