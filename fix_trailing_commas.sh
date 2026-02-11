#!/bin/bash

# List of problematic files
problematic="TU-2357 TU-2492 TU-2590 TU-2744 TU-2984 TU-4759 TU-4796 TU-5092 TU-5214 TU-5247"

for patient_id in $problematic; do
    file="json/${patient_id}_ngs.json"
    echo "Fixing: $file"
    
    # Remove trailing commas before } or ]
    # This regex finds ", }" or ",}" and replaces with just "}"
    sed -i 's/,\s*}/}/g' "$file"
    sed -i 's/,\s*]/]/g' "$file"
    
    # Verify
    if jq empty "$file" 2>/dev/null; then
        echo "  ✓ Fixed successfully"
    else
        echo "  ✗ Still has errors"
        jq . "$file" 2>&1 | head -3
    fi
done

echo ""
echo "All done!"
