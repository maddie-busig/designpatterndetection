#!/usr/bin/bash

# Not gonna lie, I forget what this one was for...

if [ $# -lt 3 ]; then
	echo "NOT ENOUGH ARGUMENTS"
	echo "USAGE: sort_patterns.sh INPUT_SPLIT PREDICTIONS OUTPUT"
fi

header_line='project_name,class_name,num_pattern,pattern'

input_dir=$1
predictions_file=$2
output_dir=$3

while read line; do
	if [[ $line = $header_line ]]; then
		continue
	fi

	entry_arr=(${line//,/ })

	project=${entry_arr[0]}
	class=${entry_arr[1]}
	pattern=${entry_arr[3]}

	project_dir="$input_dir/$project"
	input_file=$(find "$project_dir" -name "$class.java" -print -quit)
	relative_file=${input_file#${input_dir}/}

	output_file="$output_dir/$pattern/$relative_file"
	file_dir=$(dirname "$output_file")

	echo "$project, $class - $pattern ($input_file) ($output_file)"

	mkdir -p "$file_dir"
	cp "$input_file" "$output_file"
done < "${predictions_file}"

