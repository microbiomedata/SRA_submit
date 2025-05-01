#!/usr/bin/env python3
__email__ = "chienchi@lanl.gov"
__author__ = "Chienchi Lo"
__version__ = "2.0"
__update__ = "07/02/2024"
__project__ = "National Microbiome Data Collaborative"

import os
import sys
import json
import argparse
import subprocess
import logging
import xml.etree.ElementTree as ET
import time

def ValidateLog(xml_file):
    """Parse and display the validation result from NCBI"""
    try:
        t = ET.ElementTree(file=xml_file).getroot()
    except ET.ParseError as e:
        print(f"⚠️ Failed to parse XML response: {e}")
        with open(xml_file, 'r') as f:
            print("Raw response content:")
            print(f.read())
        return None

    msg = {}
    status = t.find("Action").attrib.get("status", "unknown")
    s = {"processed-error": "No", "failed": "No", "processed-ok": "Yes", "submitted": "No", "processing": "No"}
    msg["Passed"] = s.get(status, "Unknown")
    if t.find("Action/Response/Message") is not None:
        msg["Report Text"] = t.find("Action/Response/Message").text
    print(json.dumps(msg, indent=2))
    return t

def extract_sample_id(adddata_element):
    """Extract sample ID from <SampleId>/<SPUID>"""
    spuid_elem = adddata_element.find(".//SampleId/SPUID")
    if spuid_elem is not None and spuid_elem.text:
        return spuid_elem.text.strip()
    return "Unknown_Sample"

def validate_each_adddata(input_file, final_output_path):
    tree = ET.parse(input_file)
    root = tree.getroot()
    ncbi_validate_service_api = "https://www.ncbi.nlm.nih.gov/projects/biosample/validate/"

    combined_root = ET.Element("ValidationResponses")

    for idx, adddata in enumerate(root.findall(".//AddData"), 1):
        sample_id = extract_sample_id(adddata)
        print(f"Validating Biosample block {idx} (SampleId: {sample_id})...")

        # Write the AddData block to a temp file
        temp_file = f"temp_block_{idx}.xml"
        ET.ElementTree(adddata).write(temp_file)

        # Call the validation API
        response_file = f"temp_response_{idx}.xml"
        with open(response_file, "w") as rp:
            subprocess.call(["curl", "-s", "-X", "POST", "-d", f"@{temp_file}", ncbi_validate_service_api], stdout=rp)

        # Parse the response and append it to the combined output
        response_root = ValidateLog(response_file)
        if response_root is not None:
            combined_root.append(response_root)

        # Clean up temporary files
        os.remove(temp_file)
        os.remove(response_file)
        time.sleep(1)

    # Write combined response XML
    combined_tree = ET.ElementTree(combined_root)
    combined_tree.write(final_output_path)
    print(f"✅ All validation responses saved to: {final_output_path}")


def main(argvs):
    submission_xml = argvs.input_file
    validate_xml = argvs.output_xml
    validate_each_adddata(submission_xml,validate_xml)


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
