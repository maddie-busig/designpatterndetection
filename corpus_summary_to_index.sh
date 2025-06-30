#!/usr/bin/bash

infile=$1
outfile=$2

sed -E "1,3d;s/(.*), (.*)\.java /\1,\2,NA/g;s/PROJECT, CLASS/Project,Class,Pattern/g" "${infile}" > "${outfile}"

