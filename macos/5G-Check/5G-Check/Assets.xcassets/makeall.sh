#!/usr/bin/env bash

INKSCAPE=/Applications/Inkscape.app/Contents/MacOS/inkscape
SRC=5g-check.svg
DST=AppIcon.appiconset

mkdir -p ${DST}
for i in 16 32 128 256 512
do
    ${INKSCAPE} -o ${DST}/icon_$ix$i.png -C --export-width=$i --export-height=$i --export-overwrite ${SRC}
    ${INKSCAPE} -o ${DST}/icon_$ix$i@2x.png -C --export-width=$(($i * 2)) --export-height=$(($i * 2)) --export-overwrite ${SRC}
done

# iconutil --convert icns ${DST}

DST=icons

mkdir -p ${DST}
for i in 16 32 48 64 96 128 256
do
    ${INKSCAPE} -o ${DST}/$i.png -C --export-width=$i --export-height=$i --export-overwrite ${SRC}
done

