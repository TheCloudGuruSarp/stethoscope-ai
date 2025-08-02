#!/bin/bash
# Stethoscope AI - Secure Snapshot Script v3.1
# This script is read-only and outputs Base64 encoded JSON.
# Fix: Correctly assembles the final JSON object to be valid.

# Exit immediately if a command exits with a non-zero status.
set -e
set -o pipefail

# This function encodes the collected JSON data into Base64.
encode_and_output() {
    local data="$1"
    # Encode the data into Base64. The -w 0 flag prevents line wrapping.
    echo "$data" | base64 -w 0
}

# --- DATA COLLECTION FUNCTIONS ---
# Each function now prints a JSON key-value pair WITH a trailing comma.

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
    printf '"performance": {'
    printf '"load_average": "%s",' "$(cat /proc/loadavg | awk '{print $1, $2, $3}')"
    printf '"uptime_seconds": %s,' "$(cat /proc/uptime | awk '{print $1}')"
    printf '"running_processes": %s' "$(ps -e --no-headers | wc -l)"
    printf '},'
}

get_memory_info() {
    local mem_info
    mem_info=$(</proc/meminfo)
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

get_top_processes() {
    # This is the LAST data function, so it should NOT have a trailing comma.
    printf '"top_processes": ['
    ps_output=$(ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu | head -n 6 | tail -n 5 && ps -eo pid,user,%cpu,%mem,comm --sort=-%mem | head -n 6 | tail -n 5)
    
    first_line=true
    echo "$ps_output" | while read -r line; do
        if [ -z "$line" ]; then continue; fi
        if [ "$first_line" = false ]; then
            printf ','
        fi
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

# --- MAIN FUNCTION: ASSEMBLE ALL DATA ---
main() {
    # Assemble the final JSON string correctly.
    json_output=$(printf '{%s%s%s%s%s%s}' \
      "$(get_os_info)" \
      "$(get_hardware_info)" \
      "$(get_performance_info)" \
      "$(get_memory_info)" \
      "$(get_disk_info)" \
      "$(get_top_processes)" \
    )

    # Encode the final JSON and print it to stdout
    encode_and_output "$json_output"
}

# Run the main function
main
