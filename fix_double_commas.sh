#!/bin/bash

# Fix double commas in JSON files
for patient_id in $(cat missing_patients.txt); do
    file="json/${patient_id}_ngs.json"
    echo "Fixing: $file"
    
    # Replace double commas with single comma
    sed -i 's/,,/,/g' "$file"
    
    # Verify it's now valid JSON
    if jq empty "$file" 2>/dev/null; then
        echo "  ✓ Fixed successfully"
    else
        echo "  ✗ Still has errors"
    fi
done

echo ""
echo "Done! Re-run your extraction script now."
