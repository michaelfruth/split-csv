import os
from argparse import ArgumentParser
import csv
from typing import List, Any, Optional
from operator import itemgetter
from itertools import groupby
import re

DELIMITER = ";"

class CSVData:

    def __init__(self, header: List[str], data: List[List[Any]]) -> None:
        self.header: List[str] = header
        self.data: List[List[Any]] = data

    def __str__(self) -> str:
        return DELIMITER.join(self.header) + "\n" + "\n".join(DELIMITER.join(d) for d in self.data)

def read_csv(file: str) -> CSVData:
    with open(file) as f:
        reader = list(csv.reader(f, delimiter=DELIMITER))
        header = reader[0]
        data = reader[1:]
    return CSVData(header, data)


def ignore_data(csv_data: CSVData, ignore_columns: List[str]) -> None:
    if not ignore_columns:
        return
    ignore_regexes: List[re.Pattern] = [re.compile(column_name) for column_name in ignore_columns]

    column_indices_to_ignore: List[int] = sorted(list({idx for regex in ignore_regexes for idx, header in enumerate(csv_data.header) if regex.match(header)}))

    removed = 0
    for ignore_column_index in column_indices_to_ignore:
        del csv_data.header[ignore_column_index - removed]
        for data in csv_data.data:
            del data[ignore_column_index - removed]
        removed += 1

def match_groups_to_indices(csv_data: CSVData, groups: List[int]):
    def is_in_group(group: str) -> bool:
        if group not in csv_data.header:
            print(f"Group '{group}' is not available. Available groups are {csv_data.header}. This group will be ignored.")
            return False
        return True

    return [csv_data.header.index(group) for group in groups if is_in_group(group)]


def split_data_by_groups(csv_data: CSVData, indices: List[int]) -> List[CSVData]:
    if len(indices) == 0:
        return []
    data = csv_data.data[:] # Copy list
    data.sort(key=itemgetter(*indices))
    return [CSVData(csv_data.header, list(value)) for key, value in groupby(data, itemgetter(*indices))]


def export_data(csv_data: List[CSVData], output: str) -> None:
    if len(csv_data) == 0:
        return
    if not os.path.isdir(output):
        os.mkdir(output)

    for idx, output_csv_data in enumerate(csv_data):
        csv_output_file = os.path.join(output, f"{idx}.csv")
        pdf_output_file = os.path.join(output, f"{idx}.pdf")
        with open(csv_output_file, "w") as f:
            writer = csv.writer(f, delimiter=DELIMITER)
            writer.writerow(output_csv_data.header)
            writer.writerows(output_csv_data.data)


def main():
    parser = ArgumentParser()
    parser.add_argument("--csv", help="The path to the csv file.", required=True)
    parser.add_argument("--groups", help="The groups to group. For each group, a PDF is created.", nargs="+", required=True)
    parser.add_argument("--ignore-regexes", help="The columns to ignore. Regex supported.", nargs="+")
    parser.add_argument("--output", help="The output directory in which the exported PDF files are stored", required=True)

    args = parser.parse_args()
    csv_data: CSVData = read_csv(args.csv)
    print(csv_data.header)
    ignore_data(csv_data, args.ignore_regexes)
    indices: List[int] = match_groups_to_indices(csv_data, args.groups)
    splitted_data = split_data_by_groups(csv_data, indices)
    export_data(splitted_data, args.output)



