#!/bin/bash
# Find and fix all citation mismatches

echo "Finding correct citation keys..."

# Build mapping of wrong keys to correct keys
declare -A MAPPING

# Check each undefined citation
for wrong in "Coste_2010" "grauers2012genetics" "negrini2018scientific" "stokes2007hueter" \
             "weinstein2013bracing" "white1990clinical" "chesler2016piezo2" "domenech2016melatonin" \
             "kouwenhoven2006organ" "lynch2015bioenergetic" "Meyer_2021" "newton2005differential" "wei2015sirt1"; do
    
    # Extract author and year
    AUTHOR=$(echo "$wrong" | sed 's/[_0-9].*//;s/[0-9].*//')
    YEAR=$(echo "$wrong" | grep -o '[0-9]\+')
    
    # Find correct key in bib file
    CORRECT=$(grep -i "^@.*$AUTHOR.*$YEAR\|^@.*{$AUTHOR$YEAR" references.bib | head -1 | sed 's/@[^{]*{\([^,]*\).*/\1/')
    
    if [ -n "$CORRECT" ]; then
        echo "  $wrong → $CORRECT"
        MAPPING["$wrong"]="$CORRECT"
    else
        echo "  ❌ $wrong → NOT FOUND"
    fi
done

echo ""
echo "Applying fixes to all section files..."

for file in sections/*.tex; do
    if [ -f "$file" ]; then
        for wrong in "${!MAPPING[@]}"; do
            correct="${MAPPING[$wrong]}"
            if grep -q "$wrong" "$file"; then
                sed -i "s/$wrong/$correct/g" "$file"
                echo "  Fixed $wrong → $correct in $(basename $file)"
            fi
        done
    fi
done

echo ""
echo "✅ Citation fixes applied"
