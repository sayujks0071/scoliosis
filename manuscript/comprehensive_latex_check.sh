#!/bin/bash
echo "═══════════════════════════════════════════════════════════"
echo "COMPREHENSIVE LATEX VERIFICATION"
echo "═══════════════════════════════════════════════════════════"
echo ""

CRITICAL_ERRORS=0
WARNINGS=0

# 1. Check main.tex can find all inputs
echo "1. Verifying all \input files exist..."
while IFS= read -r line; do
    if [[ $line =~ \\input\{([^}]+)\} ]]; then
        FILE="${BASH_REMATCH[1]}.tex"
        if [ ! -f "$FILE" ]; then
            echo "  ❌ CRITICAL: Missing $FILE"
            ((CRITICAL_ERRORS++))
        else
            echo "  ✅ $FILE"
        fi
    fi
done < main.tex

echo ""
echo "2. Checking references.bib exists and is valid..."
if [ ! -f "references.bib" ]; then
    echo "  ❌ CRITICAL: references.bib missing"
    ((CRITICAL_ERRORS++))
else
    ENTRIES=$(grep -c "^@" references.bib)
    echo "  ✅ references.bib exists ($ENTRIES entries)"
    # Check for common bib errors
    if grep -q "^@.*{,$" references.bib; then
        echo "  ⚠️  WARNING: Empty citation keys found"
        ((WARNINGS++))
    fi
fi

echo ""
echo "3. Checking for undefined cross-references..."
# Get all \ref commands
grep -roh "\\\\ref{[^}]*}" sections/*.tex | sed 's/\\ref{\([^}]*\)}/\1/' | sort -u > /tmp/all_refs.txt
# Get all \label commands from ALL files
grep -roh "\\\\label{[^}]*}" sections/*.tex | sed 's/\\label{\([^}]*\)}/\1/' | sort -u > /tmp/all_labels.txt

UNDEFINED=$(comm -23 /tmp/all_refs.txt /tmp/all_labels.txt)
if [ -n "$UNDEFINED" ]; then
    echo "  ❌ CRITICAL: Undefined references found:"
    echo "$UNDEFINED" | while read ref; do
        echo "    • $ref"
        ((CRITICAL_ERRORS++))
    done
else
    echo "  ✅ All references have labels"
fi

echo ""
echo "4. Checking for undefined citations..."
# Get all cite keys
grep -roh "\\\\cite{[^}]*}" sections/*.tex | sed 's/\\cite{\([^}]*\)}/\1/' | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v "^$" | sort -u > /tmp/all_cites.txt
# Get all bib keys
grep "^@" references.bib | sed 's/@[^{]*{\([^,]*\).*/\1/' | sort -u > /tmp/all_bibkeys.txt

MISSING_CITES=$(comm -23 /tmp/all_cites.txt /tmp/all_bibkeys.txt)
if [ -n "$MISSING_CITES" ]; then
    echo "  ❌ CRITICAL: Citations not in bibliography:"
    echo "$MISSING_CITES" | while read cite; do
        echo "    • $cite"
        ((CRITICAL_ERRORS++))
    done
else
    echo "  ✅ All citations have bibliography entries"
fi

echo ""
echo "5. Checking for figure files..."
MISSING_FIGS=0
grep "\\includegraphics" sections/figures.tex | grep -o "{[^}]*}" | tr -d '{}' | while read fig; do
    # Check multiple possible locations
    if [ -f "figures/$fig" ] || [ -f "../alphafold_figures/$fig" ] || [[ "$fig" =~ ^\.\./ ]]; then
        echo "  ✅ $fig"
    else
        echo "  ⚠️  WARNING: Cannot find $fig"
        ((MISSING_FIGS++))
    fi
done

echo ""
echo "6. Checking for common LaTeX errors..."
# Check for $$ in text (should use \[ \])
if grep -q '\$\$' sections/*.tex; then
    echo "  ⚠️  WARNING: Found $$ (use \\[ \\] instead)"
    ((WARNINGS++))
else
    echo "  ✅ No $$ found"
fi

# Check for unescaped special characters
if grep -P '[^\\][%&#]' sections/*.tex | grep -v "^%" | head -1 > /dev/null; then
    echo "  ⚠️  WARNING: Possible unescaped special characters"
    ((WARNINGS++))
else
    echo "  ✅ Special characters look escaped"
fi

echo ""
echo "7. Checking document structure..."
if grep -q "\\documentclass" main.tex; then
    echo "  ✅ \\documentclass present"
else
    echo "  ❌ CRITICAL: No \\documentclass"
    ((CRITICAL_ERRORS++))
fi

if grep -q "\\begin{document}" main.tex; then
    echo "  ✅ \\begin{document} present"
else
    echo "  ❌ CRITICAL: No \\begin{document}"
    ((CRITICAL_ERRORS++))
fi

if grep -q "\\end{document}" main.tex; then
    echo "  ✅ \\end{document} present"
else
    echo "  ❌ CRITICAL: No \\end{document}"
    ((CRITICAL_ERRORS++))
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "SUMMARY"
echo "═══════════════════════════════════════════════════════════"
echo "Critical errors: $CRITICAL_ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ "$CRITICAL_ERRORS" -eq 0 ]; then
    echo "✅ ✅ ✅ NO CRITICAL ERRORS - WILL COMPILE ✅ ✅ ✅"
    echo ""
    echo "The manuscript is ready for Overleaf compilation."
    exit 0
else
    echo "❌ CRITICAL ERRORS FOUND - COMPILATION WILL FAIL"
    echo ""
    echo "Fix the errors above before uploading to Overleaf."
    exit 1
fi
