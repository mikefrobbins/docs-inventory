# Script to take the output of take-inventory.py or extract-metadata.py (.csv files), and
# consolidate the entries by filename, making columns for the different terms involved (and count).
# The terms are loaded from terms.txt and are used to make the columns.
#
# Other fields are left as-is
#
# take-inventory.py invokes this script automatically at the end of its processing using the output from
# extract-metadata.py.
#
# Note that this script depends on the CSV file being sorted by filename, as take-inventory.py produces.

import sys
from utilities import parse_folders_terms_arguments

_, terms_file, args = parse_folders_terms_arguments(sys.argv[1:])

if terms_file == None:
    print("Usage: python consolidate.py --terms=<terms_file> <input_csv_file.csv>")
    print("<input_csv_file.csv> is the output from take-inventory.py or extract-metadata.py and should be sorted by filename.")
    print("<terms_file> should be the same one given to take-inventory.py.")
    sys.exit(2)

# Making the output filename assumes the input filename has only one .
input_file = args[0]
elements = input_file.split('.')
output_file = elements[0] + '-consolidated.' + elements[1]

print("consolidate: Starting consolidation")

terms = [line.rstrip('\n') for line in open(terms_file)]

# Clear out unused terms and strip off the L/R/# indicators, leaving only
# a list of raw terms that are in use.
used_terms = []

for term in terms:    
    terms_info = term.split(None, 1)    

    if not terms_info[0].startswith('#'):
        used_terms.append(terms_info[1])

terms = used_terms

with open(input_file, encoding='utf-8') as f_in:
    import csv    
    reader = csv.reader(f_in)    
    headers = next(reader)
    
    # Replace "Term" columns with individual terms; also remove Line and Extract (not meaningful)
    index_term = headers.index("Term")
    index_line = headers.index("Line")
    index_extract = headers.index("Extract")    
    headers.remove("Term")
    headers.remove("Line")
    headers.remove("Extract")

    # Insert columns for each of the terms, plus a "Term Total" column
    for i in range(0, len(terms)):
        headers.insert(index_term + i, terms[i])        

    headers.insert(index_term + i + 1, "Term Total")

    with open(output_file, 'w', encoding='utf-8', newline='') as f_out:        
        writer = csv.writer(f_out)
        writer.writerow(headers)

        term_counts = [0] * len(terms)
        current_row = next(reader)

        while (True):
            if current_row == None:
                break

            next_row = next(reader, None)  # Assigns None if we're at the end

            term = current_row[index_term]
            term_counts[terms.index(term)] += 1

            # If the filename in the next row is the same, continue with the next line
            if next_row != None and current_row[1] == next_row[1]:
                current_row = next_row
                continue;

            # Otherwise, write the term count columns
            # First, remove the Extract, Line, and Term columns, which are no longer relevant.
            # We do this in reverse order because we're using indices. Note that this does assume
            # the ordering generated by take-inventory.py and extract-metadata.py.
            current_row.pop(index_extract)
            current_row.pop(index_line)
            current_row.pop(index_term)

            total = 0

            for i in range(0, len(terms)):
                current_row.insert(index_term + i, term_counts[i])                
                total += term_counts[i]

            # Add one more row with the total count of terms, which accomodates sorting
            current_row.insert(index_term + i + 1, total)

            # Write the row
            writer.writerow(current_row)

            # Reset state for the next round, including the counts
            current_row = next_row
            term_counts = [0] * len(terms)

print("consolidate: Consolidation complete")
