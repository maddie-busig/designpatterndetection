# NOTE: Using Python 2.7 because that's the version used for other scripts in proj

import sys
import os
import pandas
import shutil
import re
import errno
from distutils.dir_util import copy_tree

# Gets the name of the package containing the Java class
def get_package(filename):
    match = None;
    with open(filename, "r") as file:
        source = file.read()

        # Find first match of package line. ex:
        # package com.Foo.Bar;
        match = re.search("(?m)^package\s+([\w\.]+);", source)

    if match is None:
        return None

    package = match.group(1)
    
    return package

# Finds all subprojects of a given project inside the corpus. Uses the package
# listed inside each of the .java files and uses that to get the src directory
# Returns a list of the subproject directories
def find_subprojects(in_corpus_dir, project_name):
    project_dir = os.path.join(in_corpus_dir, project_name)

    print "Finding subprojects of directory", project_dir

    subproj_dirs = []

    for root, dirs, files in os.walk(project_dir):
        for filetail in files:
            filename = os.path.join(root, filetail)

            # Ignore java files
            if not filename.endswith(".java"):
                continue

            package = get_package(filename)
            if package is None:
                print "File", filename, "does not have package! skipping..."
                continue

            # Converting root directory to a "package" and checking against the
            # actual package because some directories contain periods
            root_as_package = root.replace("/", ".")

            if not root_as_package.endswith(package):
                print "Root of", filename, "does not match package name! skipping..."
                continue

            # Using suffix length to get substring because removesuffix wasn't added until 3.9 :/
            # Add one to remove trailing slash character
            suffix_len = len(package) + 1
            srcdir = root[:-suffix_len]

            # Get path from corpus directory because this will be output to CSV later
            srcdir = os.path.relpath(srcdir, in_corpus_dir)

            if srcdir not in subproj_dirs:
                subproj_dirs.append(srcdir)

    print "Found subprojects:", subproj_dirs

    return subproj_dirs

def filter_tests(subproj_dirs, whitelist):
    num_filtered = 0

    num_before = len(subproj_dirs);

    filtered_dirs = []
    test_subproj_dirs = []

    for dir in subproj_dirs:
        if "test" in dir.lower() and dir not in whitelist:
            test_subproj_dirs.append(dir)
            subproj_dirs.remove(dir)
            num_filtered += 1

    print "Filtered", num_filtered, "subprojects"

    return subproj_dirs, test_subproj_dirs

def main():
    if len(sys.argv) < 4:
        print "Usage: find_projects IN_CORPUS_DIR OUT_CORPUS_DIR --names PROJECT_NAMES..."
        print "Usage: find_projects IN_CORPUS_DIR OUT_CORPUS_DIR PROJECT_LIST_FILE WHITELIST_FILE"
        return -1

    in_corpus_dir = sys.argv[1]
    out_corpus_dir = sys.argv[2]

    project_names = None
    whitelist = []

    if sys.argv[3] == "--names":
        project_names = sys.argv[4:]
    else:
        projects_df = pandas.read_csv(sys.argv[3])
        project_names = projects_df['Project'].to_list()

        whitelist_df = pandas.read_csv(sys.argv[4])
        whitelist = whitelist_df['Directory'].to_list()

    print "Finding subprojects of:"
    print project_names

    subproj_dirs = []

    for project_name in project_names:
        subproj_dirs += find_subprojects(in_corpus_dir, project_name)

    subproj_dirs, test_subproj_dirs = filter_tests(subproj_dirs, whitelist)

    print "----- TEST PROJECTS -----"
    print "Tests:", test_subproj_dirs

    print "----- PROJECTS -----"
    print "Mains:", subproj_dirs

    print "----- SUMMARY -----"
    print "Num test projects:", len(test_subproj_dirs)
    print "Num other projects:", len(subproj_dirs)

    subproj_df = pandas.DataFrame({ 'Directory': subproj_dirs });
    test_subproj_df = pandas.DataFrame({ 'Directory': test_subproj_dirs });

    subproj_df.to_csv("subproject_directories.csv", index=False)
    test_subproj_df.to_csv("test_subproject_directories.csv", index=False)

    print "Wrote subdirectories to CSV"
    print "Copying to projects to output directory"

    progress = 0
    tot_progress = len(subproj_dirs)

    for directory in subproj_dirs:
        in_directory = os.path.join(in_corpus_dir, directory)
        out_directory = os.path.join(out_corpus_dir, directory)

        # Using copy tree from distutils not shutils because shutils does not have
        # the dirs_exist_ok option until after python 3. W/o causes issues with some
        # projects. Using this as work around
        copy_tree(in_directory, out_directory)

        progress += 1
        print "Progress:", progress, "/", tot_progress

if __name__ == "__main__":
    main()
