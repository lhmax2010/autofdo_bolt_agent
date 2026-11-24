#!/bin/bash
# Read-only procfs enumeration. stat comm may contain spaces and parentheses.
proc_table() {
    local base=$1 table=$2 errors=$3 f line tail pid
    : > "$table"
    for f in "$base"/[0-9]*/stat; do
        if { IFS= read -r line < "$f"; } 2>> "$errors"; then
            pid=${line%% *}; tail=${line##*) }
            set -- $tail
            if test "$#" -lt 20; then printf 'invalid stat %s: %s\n' "$f" "$line" >> "$errors"; continue; fi
            printf '%s\t%s\t%s\t%s\t%s\n' "$pid" "$2" "$3" "$4" "${20}" >> "$table"
        else
            printf 'stat read failed: %s\n' "$f" >> "$errors"
        fi
    done
}
proc_descendants() {
    awk -v root="$1" 'BEGIN {selected[root]=1}
        {pid[NR]=$1;parent[$1]=$2;raw[$1]=$0}
        END {changed=1;while(changed){changed=0;for(i=1;i<=NR;i++)
          if(!selected[pid[i]] && selected[parent[pid[i]]]){selected[pid[i]]=1;changed=1}}
          for(i=1;i<=NR;i++)if(selected[pid[i]])print raw[pid[i]]}' "$2"
}
