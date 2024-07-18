#!/usr/bin/env python3

__email__ = "chienchi@lanl.gov"
__author__ = "Chienchi Lo"
__version__ = "1.0"
__update__ = "05/13/2024"
__project__ = "National Microbiome Data Collaborative"

import os
import sys
import argparse
import time
import logging
import collections
import shutil
import xml.dom.minidom

def check_report(report, db_acc):
    if not os.path.exists(report):
        logging.info("The report file %s doesn't exist" % report)
        return False, db_acc
    reportXML=xml.dom.minidom.parse(report)
    actions = reportXML.getElementsByTagName("Action")
    submission = reportXML.getElementsByTagName("SubmissionStatus")
    if submission:
        for sub in submission:
            if "processed-error" in sub.getAttributeNode("status").value or "failed" in sub.getAttributeNode("status").value:
                msg = sub.getElementsByTagName("Message")
                if msg:
                    for m in msg:
                        logging.error(m.firstChild.nodeValue)
                sys.exit(1)
            else:
                if actions:
                    for act in actions:
                        if "processed-ok" not in act.getAttributeNode("status").value:
                            msg = act.getElementsByTagName("Message")
                            if msg:
                                for m in msg:
                                    logging.info("%s %s %s" % (act.getAttributeNode("target_db").value, act.getAttributeNode("status").value, m.firstChild.nodeValue ))
                            else:
                                logging.info("%s %s" % (act.getAttributeNode("target_db").value, act.getAttributeNode("status").value))
                            return False, db_acc
                        else:
                            objs=act.getElementsByTagName("Object")
                            for o in objs:
                                if o.getAttributeNode("accession"):
                                    if not db_acc[o.getAttributeNode("spuid").value]:
                                        logging.info("%s %s %s" %  (o.getAttributeNode("target_db").value, o.getAttributeNode("spuid").value, o.getAttributeNode("accession").value))
                                        db_acc[o.getAttributeNode("spuid").value][o.getAttributeNode("target_db").value] = o.getAttributeNode("accession").value
                                else:
                                    logging.info("%s %s" %  (o.getAttributeNode("target_db").value, o.getAttributeNode("spuid").value))
                                    return False, db_acc
                else:
                    return False, db_acc
    else:
        logging.error("No SubmissionStatus found")
        sys.exit(1)
        
    
    return True, db_acc

def update_sample_to_mongo(db_acc):
    return True

def main(argv):

    # use ascp get report.xml and parse it to check status
    start_time = time.time()
    time_limit = argv.max_time  #  1800 sec = 30 minutes
    dst_dir = "%s@%s:%s" % (argv.ncbi_user, "upload.ncbi.nlm.nih.gov", argv.ncbi_sra_dir)
    input_dir_name = os.path.basename(os.path.normpath(argv.input_dir))
    dst_input_dir = os.path.join(dst_dir, input_dir_name)
    remote_report_file = os.path.join(dst_input_dir, "report.xml")
    if shutil.which("ascp") is None:
        logging.error("Cannot find ascp executable")
        return False

    cmd = "ascp -q -i %s -v -T %s %s " % (argv.private_key, remote_report_file , argv.input_dir)
    local_report_file = os.path.join(argv.input_dir, "report.xml")
    success_bool = False
    ## db_acc[id][targe_db] = accession
    ## ex: {'nmdc:bsm-12-gnfpt483': {'BioSample': 'SAMN02350845'}}
    db_acc=collections.defaultdict(dict)
    while ( (time.time() - start_time) < time_limit ):
        if os.system(cmd) != 0:
            logging.info("Failed to download %s from NCBI" % remote_report_file)
        else:
            success_bool, db_acc = check_report(local_report_file,db_acc)
        
        if success_bool:
            break

        time.sleep(10) # check every 10 sec.

    ## after successfully submission and return valid db_acc, push to mongo db
    ## NMDC class OmicsProcessing slot insdc_bioproject_identifiers in the format bioproject:$accession. 
    ## NMDC class Biosample       slot insdc_biosample_identifiers  in the format biosample:$accession.
    ## NMDC class OmicsProcessing slot insdc_experiment_identifiers in the format insdc.sra:$accession.
    if (success_bool and len(db_acc) > 0 ):
        logging.info("Successfully Submit %s to NCBI" % argv.input_dir)
        #update_sample_to_mongo(db_acc)

    return(True)

if __name__ == '__main__':
    toolname = os.path.basename(__file__)
    argv = argparse.ArgumentParser( prog=toolname,
        description = "check report.xml files for the NCBI SRA submission using ascp command.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter, epilog = """
        This program is free software: you can redistribute it and/or modify it under the terms of
        the GNU General Public License as published by the Free Software Foundation, either version
        3 of the License, or (at your option) any later version. This program is distributed in the
        hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
        more details. You should have received a copy of the GNU General Public License along with
        this program. If not, see <http://www.gnu.org/licenses/>.""")
    argv.add_argument('-f', '--input-dir', dest = 'input_dir', required = True,
        help = 'Diretory where all of your FASTQ files are located.')
    argv.add_argument('-d', '--ncbi-sra-dir', dest = 'ncbi_sra_dir', required = True,
        help = 'Specify the path to the destination BioProject SRA submission folder')
    argv.add_argument('-i', '--ncbi-private-key', type = str, dest = 'private_key', required = True,
        help = 'Specify the path to your private key file.')
    argv.add_argument('-u', '--ncbi-username', dest = 'ncbi_user', required = True,
        help = 'Username for uploading files to SRA.')
    argv.add_argument('-m', '--max-time', type=int, dest = 'max_time', default = 1800, required = False,
        help = 'maximum time in sec for checking report.xml from remote site.')
    argv.add_argument('--verbose', action='store_true', help='Show more information in log')
    argv.add_argument('--version', action='version', version='%(prog)s v{version}'.format(version=__version__))

    argvs = argv.parse_args()

    log_level = logging.DEBUG if argvs.verbose else logging.INFO
    logging.basicConfig(
        format='[%(asctime)s' '] %(levelname)s: %(message)s', level=log_level, datefmt='%Y-%m-%d %H:%M')
    
    sys.exit(not main(argvs))
