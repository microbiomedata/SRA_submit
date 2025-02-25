#!/usr/bin/env python3
__email__ = "chienchi@lanl.gov"
__author__ = "Chienchi Lo"
__version__ = "1.1"
__update__ = "02/25/2025"
__project__ = "National Microbiome Data Collaborative"

import os
from urllib.request import urlretrieve
import sys
import argparse
import logging
import asyncio
import concurrent.futures

def download_url(url, out_filename):
    urlretrieve(url, out_filename)

async def download_with_semaphore(semaphore, url, out_filename):
    async with semaphore:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, download_url, url, out_filename)

async def main(argvs):
    # Create a semaphore with the specified number of threads
    semaphore = asyncio.Semaphore(argvs.threads)
    
    tasks = []

    with open(argvs.input_file, 'r') as f:
        for line in f:
            url = line.strip()
            if url.startswith("http:/") or url.startswith("https:/"):
                file_name = os.path.basename(url)
                outdir_name = argvs.output_dir
                logging.info(f"Downloading file {file_name} to {outdir_name}")
                os.makedirs(outdir_name, exist_ok=True)
                out_filename = os.path.join(outdir_name, file_name)
                
                # Create a task for each download
                task = asyncio.create_task(download_with_semaphore(semaphore, url, out_filename))
                tasks.append(task)
            else:
                logging.info("Skip file URL not start with http: %s" % url)

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    toolname = os.path.basename(__file__)
    argv = argparse.ArgumentParser(prog=toolname,
        description="download files from https to stage files for SRA submission",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, epilog="""
        This program is free software: you can redistribute it and/or modify it under the terms of
        the GNU General Public License as published by the Free Software Foundation, either version
        3 of the License, or (at your option) any later version. This program is distributed in the
        hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
        more details. You should have received a copy of the GNU General Public License along with
        this program. If not, see <http://www.gnu.org/licenses/>.""")
    argv.add_argument('-i', '--input-file', dest='input_file', required=True,
        help='a list of https url to files')
    argv.add_argument('-o', '--output-dir', dest='output_dir', required=True,
        help='staging directory')
    argv.add_argument('-t', '--threads', dest='threads', type=int, default=5,
        help='number of parallel downloads')
    argv.add_argument('--version', action='version', version='%(prog)s v{version}'.format(version=__version__))

    argvs = argv.parse_args()

    log_level = logging.INFO
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s: %(message)s', level=log_level, datefmt='%Y-%m-%d %H:%M')
    if sys.version_info >= (3, 7):
        asyncio.run(main(argvs))
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()

