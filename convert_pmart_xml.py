#!/usr/bin/python3

import os
import sys
from collections import defaultdict

import pandas
import xml.dom.minidom as minidom
from xml.dom.minidom import Document
from xml.dom.minidom import Element


def parse_entities(node):
    instances = []
    for child in node.childNodes:
        if type(child) is not Element:
            continue

        child: Element

        if child.tagName == "entity":
            role: Element = child.parentNode

            role_name = role.tagName

            # If no entity given
            if len(child.childNodes) == 0:
                continue

            fqn = child.childNodes[0].nodeValue # Get text inside node
            fqn = fqn.strip()

            instances.append((fqn, role_name))
        else:
            instances += parse_entities(child)

    return instances


def parse_pattern(pattern):
    pattern_name = pattern.getAttribute('name')

    try:
        microarchs = pattern.getElementsByTagName('microArchitectures')[0]
    except IndexError:
        print("No microarchitectures")
        return []

    print("   pattern", pattern_name)

    instances = []

    for microarch in microarchs.getElementsByTagName('microArchitecture'):
        instances += parse_entities(microarch)

    return instances


def parse_program(program):
    pattern_instances = defaultdict(dict)

    for pattern in program.getElementsByTagName('designPattern'):
        pattern_name = pattern.getAttribute('name')
        pattern_instances[pattern_name] = parse_pattern(pattern)

    return pattern_instances


# Parse patterns from PMart XML 'designPatterns' node
def parse_patterns(dps_xml_element):
    program_patterns = defaultdict(dict)

    for program in dps_xml_element.getElementsByTagName('program'):
        program_name = program.getElementsByTagName('name')[0].firstChild.nodeValue
        print("Parsing program", program_name)

        program_patterns[program_name] = parse_program(program)

    return program_patterns


def main():
    if len(sys.argv) < 3:
        print('Usage: convert_pmart_xml.py PMART_LIST_XML OUTPUT_CSV')
        print('Converts a PMart XML design pattern list into a CSV format')
        print('suitable for DPDf')
        exit(-1)

    pmart_xml_filename = sys.argv[1]
    output_csv_filename = sys.argv[2]

    dom = minidom.parse(pmart_xml_filename)
    dom: Document

    design_patterns_xml_node: Element = None

    for child in dom.childNodes:
        child: Element

        if child.nodeName == 'designPatterns':
            design_patterns_xml_node = child
            break

    pattern_instances = parse_patterns(design_patterns_xml_node)

    programs = []
    for prog in pattern_instances.keys():
        programs += [
                {'Project': prog, 'Pattern': pattern}
                for pattern in pattern_instances[prog]
                ]

    patterns_dict = []

    for pair in programs:
        program = pair['Project']
        pattern = pair['Pattern']

        patterns_dict += [
                {'Project': program, 'FQN': fqn, 'Pattern': pattern, 'Role': role}
                for (fqn, role) in pattern_instances[program][pattern]
                ]

    print(programs)
    print(patterns_dict)

    patterns_df = pandas.DataFrame.from_dict(patterns_dict)
    for e in patterns_df.columns:
        print(e)
    patterns_df["Class"] = patterns_df.apply(lambda row: row['FQN'].split(".")[-1], axis=1)

    patterns_df

    patterns_df.to_csv(output_csv_filename, index=False)


if __name__ == '__main__':
    main()
