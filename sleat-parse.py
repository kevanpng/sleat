#!/usr/bin/python
# -*- coding: utf-8 -*-

# Tom Porter (@porterhau5)

import xml.etree.ElementTree as etree
import optparse
import os

# return tag with namespace appropriately prepended
def fixtag(ns, tag, nsmap):
    return '{' + nsmap[ns] + '}' + tag

# return empty string instead of None
def xstr(s):
    if s is None:
        return ''
    return str(s)


def main():
    usage = ("Usage: %prog INFILE [-o OUTFILE]"
          "\n\nAn XML parser for output generated by python-evtx. Parses input "
          "XML file and pulls fields related to Logon events (EventID 4624)."
          "\nSorts and removes duplicates records. By default writes output to "
          "\'logons.csv\' in current working directory unless -o option is "
          "specified."
          "\n\nOutput format:"
          "\n  IpAddress,TargetDomainName,TargetUserName,WorkstationName"
          "\n\nExamples:\n  %prog CORP-dump.xml"
          "\n  %prog CORP-dump.xml -o CORP-logons.csv"
          "\n\nType -h or --help for a full listing of options.")
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-o',
                      dest='outfile',
                      type='string',
                      help="Write output to OUTFILE. If this option is not"
                           " specified, then will write output to "
                           "\'logons.csv\' by default in the current working"
                           " directory.")

    (options, args) = parser.parse_args()

    outfile = options.outfile

    # verify positional argument is set (INFILE)
    if len(args) == 0:
        parser.error("XML input file not set")
        exit(1)
    else:
        file_path = args[0]
        # verify input file exists
        if not os.path.isfile(file_path):
            parser.error("%s - file does not exist" % file_path)
            exit(1)

    if outfile == None:
       outfile = "logons.csv"

    print "Output file: %s" % outfile

    # initialize vars
    depth = 0
    logon = 0
    nsmap = {}
    final = []
    results = []
    ret = []

    # get an iterable
    context = etree.iterparse(file_path, events=("start", "end", "start-ns"))

    # turn it into an iterator
    context = iter(context)

    # get the root element
    event, root = context.next()

    for event, elem in context:
        # namespace handling
        if event == 'start-ns':
            ns, url = elem
            nsmap[ns] = url
        if event == 'end':
            # If EventID is 4624, continue collecting data
            if elem.tag == fixtag('', 'EventID', nsmap) and xstr(elem.text) == "4624":
                logon = 1
            if elem.tag == fixtag('', 'Data', nsmap) and logon:
                # TargetUserName
                if depth == 5:
                    ret.append(xstr(elem.text))
                    depth += 1
                # TargetDomainName
                elif depth == 6:
                    ret.append(xstr(elem.text))
                    depth += 1
                # WorkstationName
                elif depth == 11:
                    ret.append(xstr(elem.text))
                    depth += 1
                # IpAddress
                elif depth == 18:
                    ret.append(xstr(elem.text))
                    depth += 1
                else:
                    depth += 1
            # end of Event tag
            if elem.tag == fixtag('', 'Event', nsmap) and logon:
                final.append('"' + ret[3] + '","' + ret[1] + '","' + ret[0] + '","' + ret[2] + '"')
                logon = 0
                depth = 0
                ret = []
                root.clear()
    # convert to set (makes it unique)
    uniq = set(final)

    # write output to outfile
    with open(outfile, "w") as f:
        f.write('"IpAddress","Domain","AccountName","Workstation"\n')
        f.write('\n'.join(sorted(uniq)))

if __name__ == '__main__':
    main()