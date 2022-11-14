import sys, os
import xml.etree.ElementTree as etree
import json
import re

# This file is called by sembuild in order to extract csh content into pebble templates
# See https://wiki.semmle.com/pages/viewpage.action?pageId=64750889 for a description of csh
def usage_exit(error):
    if error is not None:
        print(error)
    print('Usage: python csh.py <tooltipsfile> <linksfile> <root_url> <target_dir>')
    print( '  tooltipsfile  Tooltip definitions edited in Flare.')
    print( '  linksfile     Static help link definitions edited in Flare.')
    print( '  root_url      Base url for link targets.')
    print( '  target_dir    Where to put generated files.')
    sys.exit(0 if error is None else 1)

def csh(tooltipsfile, linksfile, root_url, target_dir):
    # build a dictionary of extracted (id,content) pairs
    csh_dict = {}

    # insert all tooltips
    for key, value in map(convert_help_tooltip, extract_help_tooltips(tooltipsfile)):
        csh_dict[key] = {}
        # tooltips are put in the `text` property
        csh_dict[key]["text"] = value

    # insert all tooltips
    for key, value in map(convert_help_link(root_url), extract_help_links(linksfile)):
        if not key in csh_dict:
            csh_dict[key] = {}
        # links to static help pages are put in the `link` property
        csh_dict[key]["link"] = value

    # write the dictionary to disk    
    with open(target_dir+"/csh.peb", "w+") as f:
        f.write('{% set csh =\n')
        f.write(json.dumps(csh_dict, indent=2, sort_keys=True))
        f.write('\n%}')

# if the input file format changes, adjust this function
def extract_help_tooltips(path):
    table = etree.parse(path).find(".//table[@id='gui-text-table']")
    for row in table.findall(".//tr/td[a]"):
        key = row.find("a").get("name")
        text = "".join(row.itertext())
        yield (key, text)

def convert_help_tooltip (pair):
    key, raw_text = pair
    text = re.sub(r'\u00a0', ' ', raw_text)
    return (key, text)

def extract_help_links(path):
    table = etree.parse(path).getroot()
    for row in table.findall(".//Map"):
        key = row.get("Name")
        link = row.get("Link")
        yield (key, link)

def convert_help_link(root_url):
    def convert (pair):
        key, raw_link = pair
        rel_link = re.sub(r'^/Content/', root_url, raw_link)
        link = re.sub(r'.html', '', rel_link)
        return (key, link)
    return convert

if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) != 4:
        usage_exit(None)

    tooltipsfile = args[0]
    linksfile = args[1]
    root_url = args[2]
    target_dir = args[3]

    os.makedirs(target_dir, exist_ok=True)

    csh(tooltipsfile, linksfile, root_url, target_dir)
