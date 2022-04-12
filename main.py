import os
import pandas as pd
from optparse import OptionParser
import shutil
import glob
import time

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option(
        "--path-to-csv",
        action="store",
        type="str",
        dest="path",
        help="Path to the CSV file. \n",
    )

    parser.add_option(
        "--path-to-repository",
        action="store",
        type="str",
        dest="path_to_repository",
        help="Path to the repository folder. \n",
    )

    parser.add_option(
        "--top-n",
        action="store",
        type="str",
        dest="top_n",
        help="Top mutations to run the tornado plots on. \n",
    )

    parser.add_option(
        "--rscript",
        action="store",
        default="/home/n795d/workspace/genome-tornado-plot-wrapper/_singular_tornado_plot.R",
        type="str",
        dest="rscript",
        help="Path to the _singular_tornado_plot.R script. \n",
    )

    (options, args) = parser.parse_args()
    start_time = time.time()
    data = pd.read_csv(options.path)
    top_n = options.top_n
    path_to_repository = options.path_to_repository

    if not os.path.exists(path_to_repository):
        os.mkdir(path_to_repository)

    # Create folder of temporary .sh scripts.
    folder_of_sh_scripts = os.path.join(path_to_repository, "temp_sh_scripts")
    if os.path.exists(folder_of_sh_scripts):
        shutil.rmtree(folder_of_sh_scripts)
    os.mkdir(folder_of_sh_scripts)

    # Create .sh scripts
    png_files_to_create = []
    print("Creating sh scripts...")
    for idx, row in data.iloc[:int(top_n)].iterrows():
        chromosome = str(row["#CHROM"])
        gene = row["GENE"]
        path_to_gene_folder = os.path.join(
            path_to_repository,
            gene
        )
        if path_to_gene_folder.endswith("/"):
            path_to_gene_folder = path_to_gene_folder[:-1]

        if not os.path.exists(path_to_gene_folder):
            os.mkdir(path_to_gene_folder)
        else:
            continue
        
        path_to_sh_script = os.path.join(folder_of_sh_scripts, f"{str(idx)}.sh")
        with open(path_to_sh_script, "w") as f:
            f.write("module load R/4.0.0 \n")
            f.write(f"Rscript {options.rscript} --chromosome {chromosome} --gene {gene} --folder {path_to_gene_folder}")
        
        png_file = os.path.join(path_to_repository, gene, f"{gene}_not_zoomed.png")
        png_files_to_create.append((png_file, path_to_sh_script))


    # Call each of the .sh scripts using the bsub function.
    print("Calling sh scripts...")
    for sh_script in glob.glob(os.path.join(folder_of_sh_scripts, "*")):
        sh_scriptname = sh_script.split("/")[-1]

        num_running_jobs = int(os.popen("bjobs -r | wc -l").read())
        num_pending_jobs = int(os.popen("bjobs -p | wc -l").read())
        num_total_jobs = num_running_jobs + num_pending_jobs

        # Only send 100 jobs to the cluster at a time.
        # If more than 100 jobs, wait until there are less than 100 jobs running.
        while num_total_jobs > 100:
            num_running_jobs = int(os.popen("bjobs -r | wc -l").read())
            num_pending_jobs = int(os.popen("bjobs -p | wc -l").read())
            num_total_jobs = num_running_jobs + num_pending_jobs
            print(f"{num_total_jobs} total jobs. Sleeping 15 seconds and trying again.")
            time.sleep(15)

        # Call the command.
        command = f"bsub -J {sh_scriptname} -q medium -W 1:00 -M 10GB -R rusage[mem=10GB] < {sh_script}"
        os.popen(command)

    # Wait until there are no more running/pending jobs to check for errors.
    num_running_jobs = int(os.popen("bjobs -r | wc -l").read())
    num_pending_jobs = int(os.popen("bjobs -p | wc -l").read())
    num_total_jobs = num_running_jobs + num_pending_jobs

    while num_total_jobs != 0:
        print(f"Waiting for remaining jobs to finish... {num_total_jobs} remaining.")
        num_running_jobs = int(os.popen("bjobs -r | wc -l").read())
        num_pending_jobs = int(os.popen("bjobs -p | wc -l").read())
        num_total_jobs = num_running_jobs + num_pending_jobs
        time.sleep(10)        

    # Check which png files have not yet been created.
    remaining_files = [png_file_and_sh_script for png_file_and_sh_script in png_files_to_create if not os.path.exists(png_file_and_sh_script[0])]
    iteration = 0
    while len(remaining_files) != 0:
        print(f"Number of Remaining Files in Iteration {iteration}: {len(remaining_files)}")
        # Call the sh scripts that are still remaining.
        for png_file_and_sh_script in remaining_files:
            png_file, sh_script = png_file_and_sh_script
            sh_scriptname = sh_script.split("/")[-1]

            # Call the command.
            command = f"bsub -J {sh_scriptname}_iter{iteration} -q medium -W 1:00 -M 10GB -R rusage[mem=10GB] < {sh_script}"
            os.popen(command)

        # Wait until the number of jobs is 0 to re-try these scripts.
        num_running_jobs = int(os.popen("bjobs -r | wc -l").read())
        num_pending_jobs = int(os.popen("bjobs -p | wc -l").read())
        num_total_jobs = num_running_jobs + num_pending_jobs
        while num_total_jobs != 0:
            num_running_jobs = int(os.popen("bjobs -r | wc -l").read())
            num_pending_jobs = int(os.popen("bjobs -p | wc -l").read())
            num_total_jobs = num_running_jobs + num_pending_jobs
            time.sleep(10)

        # Update the remaining files.
        remaining_files = [png_file_and_sh_script for png_file_and_sh_script in png_files_to_create if not os.path.exists(png_file_and_sh_script[0])]
        iteration += 1

    print("Deleting sh scripts...")
    shutil.rmtree(folder_of_sh_scripts)
    print(f"DONE! Time Taken: {time.time() - start_time}")

        

