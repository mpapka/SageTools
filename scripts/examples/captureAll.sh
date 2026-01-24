#!/bin/bash
# Simple shell script to capture frames from all cameras
# Usage: ./captureAll.sh [outputDir]

outputDir="${1:-./frames}"
timestamp=$(date +%Y%m%d_%H%M%S)

mkdir -p "$outputDir"

echo "Capturing frames to $outputDir..."

# AXIS PTZ - Apiary
wget -q -O "$outputDir/axisPtzApiary_$timestamp.jpg" \
    "http://130.202.23.91/axis-cgi/jpg/image.cgi" \
    --user camera --password '0Bscura#' && echo "[OK] axisPtzApiary" || echo "[FAIL] axisPtzApiary"

# Hanwha PTZ - Apiary
wget -q -O "$outputDir/hanwhaPtzApiary_$timestamp.jpg" \
    "http://130.202.23.92/stw-cgi/video.cgi?msubmenu=snapshot&action=view" \
    --user camera --password '0Bscura#' && echo "[OK] hanwhaPtzApiary" || echo "[FAIL] hanwhaPtzApiary"

# Hanwha PTZ - ATMOS
wget -q -O "$outputDir/hanwhaPtzAtmos_$timestamp.jpg" \
    "http://130.202.23.153/stw-cgi/video.cgi?msubmenu=snapshot&action=view" \
    --user camera --password '0Bscura#' && echo "[OK] hanwhaPtzAtmos" || echo "[FAIL] hanwhaPtzAtmos"

# Mobotix Thermal - Apiary
wget -q -O "$outputDir/mobotixThermalApiary_$timestamp.jpg" \
    "http://admin:wagglesage@130.202.23.119/record/current.jpg" \
    && echo "[OK] mobotixThermalApiary" || echo "[FAIL] mobotixThermalApiary"

# Hanwha Sky-Facing Static 1 - Apiary
wget -q -O "$outputDir/hanwhaSkyApiary1_$timestamp.jpg" \
    "http://130.202.23.149/stw-cgi/video.cgi?msubmenu=snapshot&action=view" \
    --user camera --password '0Bscura#' && echo "[OK] hanwhaSkyApiary1" || echo "[FAIL] hanwhaSkyApiary1"

# Hanwha Sky-Facing Static 2 - Apiary
wget -q -O "$outputDir/hanwhaSkyApiary2_$timestamp.jpg" \
    "http://130.202.23.150/stw-cgi/video.cgi?msubmenu=snapshot&action=view" \
    --user camera --password '0Bscura#' && echo "[OK] hanwhaSkyApiary2" || echo "[FAIL] hanwhaSkyApiary2"

echo "Done."
