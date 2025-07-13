K=$1

projdir="input_projects/split_${K}"
filtdir="input_projects_filtered/split_${K}"
verbdir="input_projects_verbose/split_${K}"
datasetdir="datasets/split_${K}"
resultsdir="results/split_${K}"

train_index="input-1300.csv"
train_verbdir="built_corpus_verbose"

echo 'Filtering projects'
python build_corpus.py "${projdir}" "${filtdir}" --names $(ls $projdir)
notify-send "Finished filtering split ${K}"

echo 'Building verbose files'
python detector.py --input "${filtdir}" --output "${verbdir}" --tasks all
notify-send "Finished making verbose files for split ${K}"

./corpus_summary_to_index.sh "${verbdir}/corpus_summary.csv" "${verbdir}/class_index.csv"

mkdir -p "${datasetdir}"

combined_class_index="${datasetdir}/combined_class_index.csv"

cat "${verbdir}/class_index.csv" > "${combined_class_index}"
# Using sed to remove header from second CSV file
sed '1d' "${train_index}" >> "${combined_class_index}"

echo 'Making dataset'
python make_class_features.py "${combined_class_index}" "${datasetdir}/combined.csv" "${verbdir}" "${train_verbdir}"
notify-send "Finished making dataset for split ${K}"

python split_dataset.py "${datasetdir}/combined.csv" "${datasetdir}/train.csv" "${datasetdir}/predict.csv"

mkdir -p "${resultsdir}"

python classifier.py "${datasetdir}/train.csv" "${datasetdir}/predict.csv" "${resultsdir}"

notify-send "Finished running split ${K}"

