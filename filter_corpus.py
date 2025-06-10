# NOTE: Using Python 2.7 because thata's the version used for other scripts in proj

import sys
import os
import pandas
import shutil
from collections import defaultdict

default_output_dir = "dpdf_corpus"

# Filter column labels
property_project = "Project"
property_class = "Class"
property_pattern = "Pattern"

def print_usage():
    print "Usage:", sys.argv[0], "INPUT_DIR FILTER [OUTPUT_DIR]"
    print "  INPUT_DIR   - Input corpus directory"
    print "  FILTER      - Filter CSV containing project_name, class_name, and pattern columns. Assume CSV has headers"
    print "  OUTPUT_DIR  - Output corpus directory. Default=dpdf_corpus"

def find_class_filename(input_corpus_dir, project_name, class_name):
    project_dir = os.path.join(input_corpus_dir, project_name)

    found_filenames = []

    for root, dirs, files in os.walk(project_dir):
        for file in files:
            fileroot,ext = os.path.splitext(file) # Ignore extension
            if fileroot == class_name:
                found_filenames.append(os.path.join(root, file))

    if len(found_filenames) > 1:
        print "Found", len(found_filenames), "matches"

    return found_filenames

def build_corpus(input_corpus_dir, filter_dataframe, output_corpus_dir):
    added = defaultdict(list)
    missing = defaultdict(list)
    duplicates = defaultdict(list)

    if not os.path.isdir(output_corpus_dir):
        os.mkdir(output_corpus_dir)

    init_data = {property_project: [], property_class: [], property_pattern: []}
    columns = [ property_project, property_class, property_pattern ]
    output_dataframe = pandas.DataFrame(init_data, columns=columns)

    for index,row in filter_dataframe.iterrows():
        print row[property_project], ":", row[property_class], "--", row[property_pattern]

        project_name = row[property_project]
        class_name = row[property_class]
        pattern_name = row[property_pattern]

        # Don't process duplicates
        if class_name in added[project_name]:
            duplicates[project_name].append(class_name)
            continue

        class_filenames = find_class_filename(input_corpus_dir, project_name, class_name)

        # Don't process if missing
        if len(class_filenames) == 0:
            missing[project_name].append(class_name)
            continue

        proj_dir = os.path.join(output_corpus_dir, project_name)

        if not os.path.isdir(proj_dir):
            os.mkdir(proj_dir)

        # Copy files
        idx = 0
        for file in class_filenames:
            indexed_class_name = "{0}_{1}".format(class_name, idx)

            newfile = os.path.join(proj_dir, indexed_class_name + ".java")
            shutil.copy(file, newfile)

            idx += 1

        # Add new entry to filtered corpus list
        num_rows = len(output_dataframe)
        output_dataframe.loc[num_rows] = [ project_name, class_name, pattern_name ]
    
        added[project_name].append(class_name)

    return output_dataframe, missing, duplicates

def main():
    if len(sys.argv) < 3:
        print_usage()
        return

    input_corpus_dir = sys.argv[1]
    filter_filename = sys.argv[2]
    output_corpus_dir = default_output_dir

    if len(sys.argv) > 3:
        output = sys.argv[3]

    print "Filtering corpus", input_corpus_dir, "into", output_corpus_dir, "using filter", filter_filename

    filter_dataframe = pandas.read_csv(filter_filename)
    output_dataframe, missing, duplicates = build_corpus(input_corpus_dir, filter_dataframe, output_corpus_dir)

    print "----- Missing -----"
    num_missing = 0
    for project, classes in missing.iteritems():
        print project, "-", classes
        num_missing += len(classes)

    print "----- Duplicated -----"
    num_duplicate = 0
    for project, classes in duplicates.iteritems():
        print project, "-", classes
        num_duplicate += len(classes)

    num_found = len(filter_dataframe.index) - num_missing

    print "----- Summary -----"
    print num_found, "classes found"
    print num_missing, "classes missing"
    print num_duplicate, "classes duplicate"

    output_dataframe.to_csv("filtered_corpus.csv", index=False)

    print "Fin"

if __name__ == "__main__":
    main()

