import os
import pandas as pd
from optparse import OptionParser
import shutil
import glob
import time
import subprocess

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option(
        "-p",
        "--path-to-csv",
        action="store",
        type="str",
        dest="path",
        help="Path to the CSV file. \n",
    )

    parser.add_option(
        "-o",
        "--output-folder",
        action="store",
        type="str",
        dest="output_folder",
        help="Path to the output folder. \n",
    )

    parser.add_option(
        "-r",
        "--rscript",
        action="store",
        type="str",
        dest="rscript",
        help="Path to the _singular_tornado_plot.R script. NOTE: This must be an absolute path. \n",
    )

    parser.add_option(
        "--gtprepository",
        action="store",
        type="str",
        dest="gtprepository",
        help="Path to the GenomeTornadoPlot repository. NOTE: This must be an absolute path. \n",
    )

    parser.add_option(
        "--gtpfilesrepository",
        action="store",
        type="str",
        dest="gtpfilesrepository",
        help="Path to the folder of GenomeTornadoPlot-files repository. NOTE: This must be an absolute path. \n",
    )

    parser.add_option(
        "-d",
        "--delimiter",
        action="store",
        default="\t",
        type="str",
        dest="delimiter",
        help="Delimiter/Separator of the dataframe (i.e. ',', '\t', ';') \n",
    )

    parser.add_option(
        "-s",
        "--starting-index",
        action="store",
        default="0",
        type="str",
        dest="starting_index",
        help="Starting index of the dataframe to run GenomeTornadoPlots on. \n",
    )

    parser.add_option(
        "-e",
        "--ending-index",
        action="store",
        default="-1",
        type="str",
        dest="ending_index",
        help="Ending index of the dataframe to run GenomeTornadoPlots on. \n",
    )

    (options, args) = parser.parse_args()
    start_time = time.time()

    data = pd.read_csv(options.path, delimiter=options.delimiter)

    data = data.iloc[int(options.starting_index) : int(options.ending_index)]

    output_folder = options.output_folder

    for chromosome in data["#CHROM"].unique():
        chromosome = str(chromosome)
        if not os.path.exists(os.path.join(output_folder, f"chr{chromosome}")):
            os.mkdir(os.path.join(output_folder, f"chr{chromosome}"))

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
            gtp_command = f"Rscript {options.rscript} --chromosome {chromosome} --gene {gene} --folder {os.path.join(output_folder, f'chr{chromosome}')} --files {options.gtpfilesrepository} --repo {options.gtprepository}"
            print(f"Running {gtp_command}")
            process = subprocess.Popen(
                gtp_command.split(" "),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    print(output.strip())

            rc = process.poll()

            if process.returncode != 0:
                print(f"R script failed with return code {process.returncode}")
                for line in process.stderr:
                    print(line.strip())
        else:
            print(f"{gene}(chr{chromosome}) already exists. Skipping...")
