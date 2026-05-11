#!/bin/bash
echo "=== Checking LaTeX Syntax ==="
echo ""

# Check for common LaTeX errors
ERRORS=0

echo "1. Checking for unmatched braces..."
for file in main.tex sections/*.tex; do
    if [ -f "$file" ]; then
        OPEN=$(grep -o "{" "$file" | wc -l)
        CLOSE=$(grep -o "}" "$file" | wc -l)
        if [ "$OPEN" -ne "$CLOSE" ]; then
            echo "  ⚠️  $file: $OPEN open braces, $CLOSE close braces"
            ((ERRORS++))
        fi
    fi
done
[ "$ERRORS" -eq 0 ] && echo "  ✅ All braces balanced"

echo ""
echo "2. Checking for unmatched \begin{} \end{}..."
for file in sections/*.tex; do
    if [ -f "$file" ]; then
        grep "\\begin{" "$file" | sed 's/.*\\begin{\([^}]*\)}.*/\1/' | sort > /tmp/begins_$$.txt
        grep "\\end{" "$file" | sed 's/.*\\end{\([^}]*\)}.*/\1/' | sort > /tmp/ends_$$.txt
        DIFF=$(diff /tmp/begins_$$.txt /tmp/ends_$$.txt 2>&1)
        if [ -n "$DIFF" ]; then
            echo "  ⚠️  $file: Unmatched environments"
            ((ERRORS++))
        fi
    fi
done
[ "$ERRORS" -eq 0 ] && echo "  ✅ All environments matched"

echo ""
echo "3. Checking for undefined labels..."
CITED_LABELS=$(grep -oh "\\ref{[^}]*}" sections/*.tex | sed 's/\\ref{\([^}]*\)}/\1/' | sort -u)
DEFINED_LABELS=$(grep -oh "\\label{[^}]*}" sections/*.tex | sed 's/\\label{\([^}]*\)}/\1/' | sort -u)
MISSING=$(comm -23 <(echo "$CITED_LABELS") <(echo "$DEFINED_LABELS") | grep -v "^$")
if [ -n "$MISSING" ]; then
    echo "  ⚠️  Referenced but not defined:"
    echo "$MISSING" | sed 's/^/    /'
    ((ERRORS++))
else
    echo "  ✅ All references have labels"
fi

echo ""
echo "4. Checking for undefined citations..."
CITED_KEYS=$(grep -oh "\\cite{[^}]*}" sections/*.tex | sed 's/\\cite{\([^}]*\)}/\1/' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort -u | grep -v "^$")
BIB_KEYS=$(grep "^@" references.bib | sed 's/@[^{]*{\([^,]*\).*/\1/' | sort -u)
MISSING_CITES=$(comm -23 <(echo "$CITED_KEYS") <(echo "$BIB_KEYS") | grep -v "^$")
if [ -n "$MISSING_CITES" ]; then
    echo "  ⚠️  Cited but not in bibliography:"
    echo "$MISSING_CITES" | head -10 | sed 's/^/    /'
    ((ERRORS++))
else
    echo "  ✅ All citations defined"
fi

echo ""
echo "5. Checking for missing figure files..."
FIGURES=$(grep "\\includegraphics" sections/figures.tex | grep -o "{[^}]*}" | sed 's/[{}]//g')
for fig in $FIGURES; do
    # Check in figures/ and ../alphafold_figures/
    if [ ! -f "figures/$fig" ] && [ ! -f "../alphafold_figures/$fig" ] && [[ ! "$fig" =~ ^\.\./ ]]; then
        echo "  ⚠️  Missing: $fig"
        ((ERRORS++))
    fi
done
[ "$ERRORS" -eq 0 ] && echo "  ✅ All figures found"

echo ""
echo "=== RESULT ==="
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ No LaTeX syntax errors detected"
    echo "Manuscript should compile successfully"
else
    echo "⚠️  Found $ERRORS potential issues"
    echo "These may cause compilation errors"
fi

rm -f /tmp/begins_$$.txt /tmp/ends_$$.txt 2>/dev/null
