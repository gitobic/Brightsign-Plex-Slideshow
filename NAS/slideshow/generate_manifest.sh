#!/bin/bash
# Run this from the Mac with the NAS mounted, or via SSH on the NAS.
#
# Usage (Mac, NAS mounted at /Volumes/photo):
#   cd /Volumes/photo/slideshow
#   bash generate_manifest.sh
#
# Usage (SSH into NAS):
#   cd /volume1/photo/slideshow
#   bash generate_manifest.sh
#
# This is used to build the images.json that is readd by the plex_poller.py to select the next image for disaple
#

IMAGES_DIR="./images"
OUTPUT="./images.json"

if [ ! -d "$IMAGES_DIR" ]; then
  echo "Error: '$IMAGES_DIR' directory not found. Run from the slideshow folder."
  exit 1
fi

count=0
printf '[' > "$OUTPUT"
first=true

for f in "$IMAGES_DIR"/*.jpg "$IMAGES_DIR"/*.jpeg "$IMAGES_DIR"/*.JPG \
         "$IMAGES_DIR"/*.JPEG "$IMAGES_DIR"/*.png "$IMAGES_DIR"/*.PNG; do
  [ -f "$f" ] || continue
  name=$(basename "$f")
  # Escape any double-quotes in filename (unlikely but safe)
  name="${name//\"/\\\"}"
  if [ "$first" = true ]; then
    printf '"%s"' "$name" >> "$OUTPUT"
    first=false
  else
    printf ',"%s"' "$name" >> "$OUTPUT"
  fi
  count=$((count + 1))
done

printf ']\n' >> "$OUTPUT"

echo "Done. $count images written to $OUTPUT"
