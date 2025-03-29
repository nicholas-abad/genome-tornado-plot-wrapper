"""
This script reads a file and runs GenomeTornadoPlots for each gene.
It processes the data between specified row indices and outputs plots into chromosome-specific folders.
"""

import os
import time
import subprocess
import pandas as pd
from optparse import OptionParser

if __name__ == "__main__":
    parser = OptionParser()

    # Path to the input CSV file
    parser.add_option(
        "-p",
        "--path-to-csv",
        action="store",
        type="str",
        dest="path",
        help="Path to the CSV file. \n",
    )

    # Output folder to store plots
    parser.add_option(
        "-o",
        "--output-folder",
        action="store",
        type="str",
        dest="output_folder",
        help="Path to the output folder. \n",
    )

    # Delimiter used in the CSV file
    parser.add_option(
        "-d",
        "--delimiter",
        action="store",
        default="\t",
        type="str",
        dest="delimiter",
        help="Delimiter/Separator of the dataframe (i.e. ',', '\t', ';') \n",
    )

    # Index to start processing the CSV from
    parser.add_option(
        "-s",
        "--starting-index",
        action="store",
        default="0",
        type="str",
        dest="starting_index",
        help="Starting index of the dataframe to run GenomeTornadoPlots on. \n",
    )

    # Index to stop processing the CSV at
    parser.add_option(
        "-e",
        "--ending-index",
        action="store",
        default="-1",
        type="str",
        dest="ending_index",
        help="Ending index of the dataframe to run GenomeTornadoPlots on. \n",
    )

    (options, _) = parser.parse_args()
    start_time = time.time()

    # Load and filter the input data
    data = pd.read_csv(options.path, delimiter=options.delimiter)
    data = data.iloc[int(options.starting_index) : int(options.ending_index)]

    # Construct paths to local repositories and the R script based on script location
    output_folder = options.output_folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gtprepository = os.path.join(script_dir, "GenomeTornadoPlot")            
    path_to_rscript = os.path.join(script_dir, "_singular_tornado_plot.R")
    gtpfilesrepository = os.path.join(script_dir, "GenomeTornadoPlot-files")
            
    # Ensure all necessary paths exist
    for file in [gtprepository, path_to_rscript, gtpfilesrepository]:
        assert os.path.exists(file), file

    # Create the output directory and per-chromosome subdirectories
    os.makedirs(output_folder, exist_ok=True)

    for chromosome in data["#CHROM"].unique():
        chromosome_folder = os.path.join(output_folder, f"chr{chromosome}")
        os.makedirs(chromosome_folder, exist_ok=True)

    # Loop through each gene and run GenomeTornadoPlot if output doesn't already exist
    for idx, row in data.iterrows():
        chromosome = str(row["#CHROM"])
        gene = row["GENE"]

        # Check if this chromosome and gene already exists.
        already_exists = os.path.exists(
            os.path.join(
                output_folder,
                f"chr{chromosome}",
                f"chr{chromosome}_{gene}_not_zoomed.png",
            )
        ) and os.path.exists(
            os.path.join(
                output_folder, f"chr{chromosome}", f"chr{chromosome}_{gene}_zoomed.png"
            )
        )

        if not already_exists:
            # Construct and run the R script command
            gtp_command = f"Rscript {path_to_rscript} --chromosome {chromosome} --gene {gene} --folder {os.path.join(output_folder, f'chr{chromosome}')} --files {gtpfilesrepository} --repo {gtprepository}"
            print(f"Running {gtp_command}")
            process = subprocess.Popen(
                gtp_command.split(" "),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            while True:
                # Print stdout from the R script
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

            rc = process.poll()

            # Print stderr if the R script fails
            if process.returncode != 0:
                print(f"R script failed with return code {process.returncode}")
                for line in process.stderr:
                    print(line.strip())
        else:
            # Skip if plot images already exist
            print(f"{gene}(chr{chromosome}) already exists. Skipping...")
