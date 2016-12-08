#!/usr/bin/bash

echo
echo "Items not in the Base Runtime are in the System Runtime"
comm -1 -3 \
     base-runtime-module-definition-full.txt \
     runtime-source-packages-full.txt \
| sort | tee system-runtime-module-definition-full.txt

echo  "All remaining packages in the self-hosting list belong in gen-core-build"
cat selfhosting-source-packages-full.txt \
| sort| tee gen-core-build-module-definition-prelim.txt

cat base-runtime-module-definition-full.txt \
    system-runtime-module-definition-full.txt \
| sort | comm -2 -3 gen-core-build-module-definition-prelim.txt - \
| sort | tee gen-core-build-module-definition-full.txt


echo "Removing intermediate files"
rm -f gen-core-build-module-definition-prelim.txt

