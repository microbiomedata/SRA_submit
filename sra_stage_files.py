#!/usr/bin/env python3

__email__ = "chienchi@lanl.gov"
__author__ = "Chienchi Lo"
__version__ = "1.0"
__update__ = "07/01/2024"
__project__ = "National Microbiome Data Collaborative"

import os
from urllib.request import urlretrieve
import sys
import argparse
import logging
import asyncio

## use threads to async IO-bound loop
def background(f):
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, **kwargs)
    return wrapped

@background
def dowload_url(url,out_filename):
    
    urlretrieve(url,out_filename)


def main(argvs):

    with open(argvs.input_file,'r') as f:
        for line in f:
            url=line.strip()
            if url.startswith("http:/") or url.startswith("https:/"):
                file_name = os.path.basename(url)
                dir_name = os.path.basename(os.path.dirname(url))
                outdir_name = os.path.join(argvs.output_dir,dir_name)
                logging.info(f"Downloading file {file_name} to {outdir_name}")
                os.makedirs(outdir_name,exist_ok=True)
                out_filename=os.path.join(outdir_name,file_name)
                dowload_url(url,out_filename)
            else:
                logging.info("Skip file URL not start with http: %s" % url)
            
    return(True)

if __name__ == '__main__':
    toolname = os.path.basename(__file__)
    argv = argparse.ArgumentParser( prog=toolname,
        description = "download files from https to stage files for SRA submission",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter, epilog = """
        This program is free software: you can redistribute it and/or modify it under the terms of
        the GNU General Public License as published by the Free Software Foundation, either version
        3 of the License, or (at your option) any later version. This program is distributed in the
        hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
        more details. You should have received a copy of the GNU General Public License along with
        this program. If not, see <http://www.gnu.org/licenses/>.""")
    argv.add_argument('-i', '--input-file', dest = 'input_file', required = True,
        help = 'a list of https url to files')
    argv.add_argument('-o', '--output-dir', dest = 'output_dir', required = True,
        help = 'staging directory')
    #argv.add_argument('--verbose', action='store_true', help='Show more information in log')
    argv.add_argument('--version', action='version', version='%(prog)s v{version}'.format(version=__version__))

    argvs = argv.parse_args()

    #log_level = logging.DEBUG if argvs.verbose else logging.INFO
    log_level = logging.INFO
    logging.basicConfig(
        format='[%(asctime)s' '] %(levelname)s: %(message)s', level=log_level, datefmt='%Y-%m-%d %H:%M')
    
    sys.exit(not main(argvs))
