import re

num_tab_spaces = 4
main_regex_pattern = r'^\S+'
digits_regex_pattern = r'^\d+'

def parse_gdb_line(input_string):
    input_string = clean_gdb_string(input_string)
    starting_integers_match = re.search(digits_regex_pattern, input_string)

    if starting_integers_match:
        # Get the matched starting integers
        starting_integers = starting_integers_match.group(0)

        # Define a regular expression pattern to match the rest of the string
        rest_of_string_pattern = rf'^{starting_integers}(.*)$'

        # Find the rest of the string after the starting integers
        rest_of_string_match = re.search(rest_of_string_pattern, input_string)

        if rest_of_string_match:
            # Get the matched rest of the string
            rest_of_string = rest_of_string_match.group(1)
            #rest_of_string = clean_gdb_string(rest_of_string)
            return '{} {}'.format(starting_integers, rest_of_string)
        else:
            return 'err'
    
    # Nothing to parse here
    return input_string

def clean_gdb_string(input_string):
    input_string = input_string.replace('\\t', '' * num_tab_spaces)
    input_string = input_string.replace('\\\\n', '')
    input_string = input_string.replace('\\n', '')
    input_string = input_string.replace('\n', '')
    input_string = input_string.replace('\\"', '\"')
    input_string = input_string.replace('\"', '"')
    input_string = input_string.replace('\\', '')

    return input_string