#!/bin/sh
set -e
[ -f $1 ] || { echo "Usage: $0 <panorama file>" ; exit 1 ; }
TMP_DIR=/tmp/crowd-streamer.panorama2cubemap.$$
mkdir $TMP_DIR
cp $1 $TMP_DIR/environment.jpg
cd $TMP_DIR
wget https://aerotwist.com/static/tutorials/create-your-own-environment-maps/environment.zip
unzip environment.zip environment.blend
blender -b environment.blend -a
cd -
mv $TMP_DIR/0001.png $(dirname $1)/$(basename $1 .jpg)-pos-z.png
mv $TMP_DIR/0002.png $(dirname $1)/$(basename $1 .jpg)-neg-x.png
mv $TMP_DIR/0003.png $(dirname $1)/$(basename $1 .jpg)-neg-z.png
mv $TMP_DIR/0004.png $(dirname $1)/$(basename $1 .jpg)-pos-x.png
mv $TMP_DIR/0005.png $(dirname $1)/$(basename $1 .jpg)-neg-y.png
mv $TMP_DIR/0006.png $(dirname $1)/$(basename $1 .jpg)-pos-y.png
