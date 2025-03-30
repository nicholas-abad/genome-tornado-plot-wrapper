"""
This script reads a CSV file and runs GenomeTornadoPlots for each gene.
It processes a range of rows and outputs PNG plots into chromosome-specific folders.

Usage example:
    python main.py -p input.csv -o output_dir -d "," -s 0 -e 100
"""

import os
import time
import subprocess
import pandas as pd
from optparse import OptionParser

if __name__ == "__main__":
    # Parse command-line options
    parser = OptionParser()
    parser.add_option("-p", "--path-to-csv", type="str", dest="path", help="Path to the CSV file.")
    parser.add_option("-o", "--output-folder", type="str", dest="output_folder", help="Path to the output folder.")
    parser.add_option("-d", "--delimiter", type="str", dest="delimiter", default="\t", help="Delimiter/Separator of the dataframe (i.e. ',', '\t', ';').")
    parser.add_option("-s", "--starting-index", type="str", dest="starting_index", default="0", help="Starting index of the dataframe to run GenomeTornadoPlots on.")
    parser.add_option("-e", "--ending-index", type="str", dest="ending_index", default="-1", help="Ending index of the dataframe to run GenomeTornadoPlots on.")
    options, _ = parser.parse_args()

    start_time = time.time()

    # Load CSV and extract specified subset
    data = pd.read_csv(options.path, delimiter=options.delimiter)
    data = data.iloc[int(options.starting_index):int(options.ending_index)]

    # Set paths to R script and plot resources
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gtprepository = os.path.join(script_dir, "GenomeTornadoPlot")
    gtpfilesrepository = os.path.join(script_dir, "GenomeTornadoPlot-files")
    path_to_rscript = os.path.join(script_dir, "_singular_tornado_plot.R")

    # Ensure required paths exist
    for required_path in [gtprepository, gtpfilesrepository, path_to_rscript]:
        assert os.path.exists(required_path), f"Missing required path: {required_path}"

    # Prepare output folder
    output_folder = os.path.abspath(options.output_folder)
    os.makedirs(output_folder, exist_ok=True)

    # Create chromosome-specific folders
    for chromosome in data["#CHROM"].unique():
        os.makedirs(os.path.join(output_folder, f"chr{chromosome}"), exist_ok=True)

    # Loop through each gene and run GenomeTornadoPlot
    for _, row in data.iterrows():
        chromosome = str(row["#CHROM"])
        gene = row["GENE"]
        chr_folder = os.path.join(output_folder, f"chr{chromosome}")

        # Define output paths for both zoomed and not zoomed plots
        plot_paths = [
            os.path.join(chr_folder, f"chr{chromosome}_{gene}_not_zoomed.png"),
            os.path.join(chr_folder, f"chr{chromosome}_{gene}_zoomed.png")
        ]

        # Skip plotting if both plots already exist
        if all(os.path.exists(path) for path in plot_paths):
            print(f"{gene}(chr{chromosome}) already exists. Skipping...")
            continue

        # Build Rscript command
        gtp_command = [
            "Rscript", path_to_rscript,
            "--chromosome", chromosome,
            "--gene", gene,
            "--folder", chr_folder,
            "--files", gtpfilesrepository,
            "--repo", gtprepository
        ]

        print(f"Running: {' '.join(gtp_command)}")

        # Run the R script and capture output
        process = subprocess.Popen(gtp_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for stdout_line in iter(process.stdout.readline, ""):
            if stdout_line:
                print(stdout_line.strip())
        process.stdout.close()

        return_code = process.wait()

        # Handle R script errors
        if return_code != 0:
            print(f"R script failed with return code {return_code}")
            for err_line in process.stderr:
                print(err_line.strip())
        process.stderr.close()
