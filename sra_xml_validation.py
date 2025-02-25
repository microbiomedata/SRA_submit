#!/usr/bin/env python3

__email__ = "chienchi@lanl.gov"
__author__ = "Chienchi Lo"
__version__ = "1.0"
__update__ = "07/02/2024"
__project__ = "National Microbiome Data Collaborative"

import os
import sys
import json
import argparse
import subprocess
import logging
import xml.etree.ElementTree as ET

def ValidateLog(f):
    """ output the validate.xml content to logfile """
    msg = {}
    t = (ET.ElementTree(file = f)).getroot()
    """
    with open(f, "w") as fl:
        fl.write("message: %s\n" % t.find("Action/Response/Message").text)
        fl.write("sample_id: %s\n" % t.find("Action/Response/Object").attrib["spuid"])
    """
    s = {"processed-error": "No", "failed": "No", "processed-ok": "Yes", "submitted": "No", "processing": "No"}
    msg["Passed"] = s[t.find("Action").attrib["status"]]
    if t.find("Action/Response/Message") is not None:
        msg["Report Text"] = t.find("Action/Response/Message").text
    print(json.dumps(msg))
    return(0 if msg["Passed"] == "Yes" else 1)

def main(argvs):

    validate_xml = argvs.output_xml
    submission_xml = argvs.input_file
    ncbi_validate_service_api = "https://www.ncbi.nlm.nih.gov/projects/biosample/validate/" 
    logging.info("Validate %s by NCBI" % submission_xml)
    with open(validate_xml, "w") as rp:
        subprocess.call(["curl", "-X", "POST", "-d", "@%s" % submission_xml, 
                         ncbi_validate_service_api], stdout = rp)

    return(ValidateLog(validate_xml))

if __name__ == '__main__':
    toolname = os.path.basename(__file__)
    argv = argparse.ArgumentParser( prog=toolname,
        description = "validate sumbission xml through NCBI",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter, epilog = """
        This program is free software: you can redistribute it and/or modify it under the terms of
        the GNU General Public License as published by the Free Software Foundation, either version
        3 of the License, or (at your option) any later version. This program is distributed in the
        hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
        more details. You should have received a copy of the GNU General Public License along with
        this program. If not, see <http://www.gnu.org/licenses/>.""")
    argv.add_argument('-i', '--input-file', dest = 'input_file', required = True,
        help = 'submission.xml')
    argv.add_argument('-o', '--output-file', dest = 'output_xml', default="validate.xml",
        help = 'validation result xml')
    argv.add_argument('--version', action='version', version='%(prog)s v{version}'.format(version=__version__))

    argvs = argv.parse_args()

    log_level = logging.INFO
    logging.basicConfig(
        format='[%(asctime)s' '] %(levelname)s: %(message)s', level=log_level, datefmt='%Y-%m-%d %H:%M')
    
    sys.exit(not main(argvs))
