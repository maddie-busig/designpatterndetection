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

def find_class_occurences(project_name, class_name, corpus_dir):
    project_dir = os.path.join(corpus_dir, project_name)

    found_filename = None
    matches_found = 0

    for root, dirs, files in os.walk(project_dir):
        for file in files:
            fileroot,ext = os.path.splitext(file) # Ignore extension
            if fileroot == class_name:
                found_filename = os.path.join(root, file)
                matches_found += 1

    if matches_found == 1:
        return matches_found, found_filename
    else:
        print "Found", matches_found, "matches"
        return matches_found, None

def path_to_fully_qualified_name(corpus_dir, project_name, class_path):
    # Using name from path relative to project directory for now. GitHub corpus
    # doesn't seem super consistent about how its projects are structured :/
    # Checking for "com", "org", etc could help somewhat, but some projects
    # have a wildly different structure (esp. bigish ones)
    project_dir = os.path.join(corpus_dir, project_name)

    rel_path = os.path.relpath(class_path, project_dir)

    fq_name = rel_path.replace('/', '.')
    print "fqname:", fq_name
    
    return fq_name

def add_project(project_name, input_corpus_dir, output_corpus_dir):
    srcdir = os.path.join(input_corpus_dir, project_name)
    destdir = os.path.join(output_corpus_dir, project_name)

    if not os.path.isdir(srcdir):
        print "Project does not exist"
    else:
        print "Adding project", project_name
        shutil.copytree(srcdir, destdir)

def build_corpus(input_corpus_dir, filter_dataframe, output_corpus_dir):
    added_projects = list()

    # Make output corpus dir
    if not os.path.isdir(output_corpus_dir):
        os.mkdir(output_corpus_dir)

    output_labels = []
    missing = []
    multiple_files = []
    multiple_listed = []

    # Pandas DataFrame.value_counts doesn't exist until v1.3.0 :(
    filter_occurence_counts = defaultdict(dict)

    for index,row in filter_dataframe.iterrows():
        project_name = row[property_project]
        class_name = row[property_class]

        if not project_name in filter_occurence_counts or not class_name in filter_occurence_counts[project_name]:
            filter_occurence_counts[project_name][class_name] = 1
        else:
            filter_occurence_counts[project_name][class_name] += 1

    for index,row in filter_dataframe.iterrows():
        project_name = row[property_project]
        class_name = row[property_class]
        pattern_name = row[property_pattern]

        print project_name, ":", class_name, "--", pattern_name

        if not project_name in added_projects:
            add_project(project_name, input_corpus_dir, output_corpus_dir)
            added_projects.append(project_name)

        times_listed = filter_occurence_counts[project_name][class_name]

        num_occurences, class_path = find_class_occurences(project_name, class_name, input_corpus_dir)

        new_row = { property_project: project_name, property_class: class_name, property_pattern: pattern_name }

        malformed = False

        if num_occurences == 0:
            print "Class missing"
            missing.append(new_row)
            malformed = True

        if times_listed > 1:
            print "Listed multiple times"
            multiple_listed.append(new_row)
            malformed = True

        if num_occurences > 1:
            print "Multiple occurences of file"
            multiple_files.append(new_row)
            malformed = True

        if not malformed:
            fq_class_name = path_to_fully_qualified_name(input_corpus_dir, project_name, class_path)

            # Add a new row to the output labels, using the fully qualified class name
            new_row[property_class] = fq_class_name
            output_labels.append(new_row)

    return output_labels, missing, multiple_files, multiple_listed

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
    output_labels, missing, multiple_files, multiple_listed = build_corpus(input_corpus_dir, filter_dataframe, output_corpus_dir)

    df_labels = [ property_project, property_class, property_pattern ]
    output_labels_df = pandas.DataFrame(output_labels, columns=df_labels)
    missing_df = pandas.DataFrame(missing, columns=df_labels)
    multiple_files_df = pandas.DataFrame(multiple_files, columns=df_labels)
    multiple_listed_df = pandas.DataFrame(multiple_listed, columns=df_labels)

    num_found = len(output_labels_df)
    num_missing = len(missing_df)
    num_mult_files = len(multiple_files_df)
    num_mult_listed = len(multiple_listed_df)

    print "----- Summary -----"
    print num_found, "classes found"
    print num_missing, "classes missing"
    print num_mult_files, "classes with multiple files"
    print num_mult_listed, "classes listed multiple times"
    
    output_labels_df.to_csv("corpus_output_labels.csv", index=False)
    missing_df.to_csv("corpus_missing.csv", index=False)
    multiple_files_df.to_csv("corpus_multiple_files.csv", index=False)
    multiple_listed_df.to_csv("corpus_multiple_listed.csv", index=False)

    print "Fin"

if __name__ == "__main__":
    main()

