#!/usr/bin/bash

input_dir=$1
n_splits=4
output_prefix='split_'

if [ $# -eq 0 ]; then
	echo 'USAGE: shuffle.sh INPUT_DIR N_SPLITS OUTPUT_PREFIX'
	exit
fi

if [ $# -gt 1 ]; then
	n_splits=$2
fi

if [ $# -gt 2 ]; then
	output_prefix=$3
fi

echo "Shuffling ${input_dir} into ${output_prefix}K with ${n_splits} splits"

input_arr=($(ls ${input_dir} | shuf))
input_count=${#input_arr[@]}

echo "Input array: ${input_arr[@]}"
echo "Input count: ${input_count}"

split_size=$((input_count/n_splits))

echo "Split size: ${split_size}"

echo shuffed: $input_str

for ((k = 0; k < n_splits; ++k)); do
	i_start=$((k * split_size))

	#for ((j = 0; j < split_size; ++j)); do
	#echo "${input_dir}${input_arr[i_start+j]}"
	#done
	split=("${input_arr[@]:${i_start}:${split_size}}")

	# If this is the last split we need to split until the end of array to not miss any elems
	if ((k == n_splits-1)); then
		split=("${input_arr[@]:${i_start}}")
	fi

	relpath_split=("${split[@]/#/${input_dir}}")

	echo "Moving split ${k}..."

	mkdir -p "${output_prefix}${k}"
	mv "${relpath_split[@]}" "${output_prefix}${k}"
done
