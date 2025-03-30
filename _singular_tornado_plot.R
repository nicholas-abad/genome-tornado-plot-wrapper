options(repos = c(CRAN = "https://cloud.r-project.org"))

# Ensure BiocManager is installed
if (!requireNamespace("BiocManager", quietly = TRUE)) {
  install.packages("BiocManager", repos = getOption("repos"))
}

# Define the list of Bioconductor packages
bioc_packages <- c('GenomicRanges', 'quantsmooth', 'IRanges')

# Function to check and install Bioconductor packages
check_and_install_bioc <- function(packages) {
  # Get the names of installed packages
  installed_packages <- installed.packages()[, "Package"]
  
  # Identify packages that are not installed
  packages_to_install <- packages[!(packages %in% installed_packages)]
  
  # Install the missing packages
  if (length(packages_to_install) > 0) {
    BiocManager::install(packages_to_install, repos = getOption("repos"))
  } else {
    message("All Bioconductor packages are already installed.")
  }
}



library("optparse")
library("ggplot2")
library("GenomeTornadoPlot")

args = commandArgs(trailingOnly=TRUE)
option_list = list(
  make_option(c("-c", "--chromosome"), type="character", default=NULL,
              help="Chromosome", metavar="character"),
  make_option(c("-g", "--gene"), type="character", default=NULL,
              help="Gene", metavar="character"),
  make_option(c("-o", "--folder"), type="character", default=".",
              help="Output folder of Plots", metavar="character"),
  make_option(c("-f", "--repo"), type="character", default="./GenomeTornadoPlot/",
              help="Path to the genome tornado plot repository.", metavar="character"),
  make_option(c("-r", "--files"), type="character", default="./GenomeTornadoPlot-files/",
              help="Path to the genome tornado plots files repository", metavar="character")
)
opt_parser = OptionParser(option_list=option_list)
opt = parse_args(opt_parser)

setwd(opt$repo)

devtools::install()

# Function to ensure a path ends with "/"
ensure_trailing_slash <- function(path) {
  if (!endsWith(path, "/")) {
    path <- paste0(path, "/")
  }
  return(path)
}

if (is.null(opt$chromosome) || is.null(opt$gene)){
  stop("Please specify both the chromosome and the gene.")
} else {
  print(paste("Chromosome: ", opt$chromosome))
  print(paste("Gene: ", opt$gene))
  print(paste("Output Folder: ", opt$folder))

  get_tornado_plot <- function(
    chromosome,
    gene_name,
    folder_of_plots
  ) {
    # Turn chromosome and gene_name to strings.
    chromosome <- paste(chromosome)
    gene_name <- paste(gene_name)

    # Load the dataset.
    path_to_rdata <- paste(ensure_trailing_slash(opt$files), "chr", chromosome, ".Rdata", sep="")
    load(path_to_rdata)

    # Rename columns.
    chr <- cnv_chr
    names(chr)[4] <- "Score"
    names(chr)[6] <- "Cohort"
    names(chr)[7] <- "PID"

    # MakeData that is necessary for generating TornadoPlots
    sdt <- MakeData(
      CNV=chr,
      gene_name_1=gene_name,
      score.type="del",
      gene_score_1=30
    )

    # Generate plots.
    not_zoomed <- TornadoPlots(
      sdt,
      color.method="ploidy",
      sort.method="length",
      multi_panel=FALSE,
      font.size.factor=1.5,
      orient="v",
      zoomed="global"
    )

    zoomed <- TornadoPlots(
      sdt,
      color.method="ploidy",
      sort.method="length",
      multi_panel=FALSE,
      font.size.factor=1.5,
      orient="v",
      zoomed="region"
    )

    # Wait 5 seconds for everything to load properly.
    Sys.sleep(5)

    # Save plots.
    path_to_not_zoomed <- paste(
      ensure_trailing_slash(folder_of_plots), "chr", chromosome, "_", gene_name, "_not_zoomed.png",
      sep=""
    )
    path_to_zoomed <- paste(
      ensure_trailing_slash(folder_of_plots), "chr", chromosome, "_", gene_name, "_zoomed.png",
      sep=""
    )
    print(paste("Path to Not Zoomed: ", path_to_not_zoomed))
    ggsave(
      file=path_to_not_zoomed,
      grid.arrange(not_zoomed[[2]])
    )

    ggsave(
      file=path_to_zoomed,
      grid.arrange(zoomed[[2]])
    )

  }

  get_tornado_plot(
    chromosome=opt$chromosome,
    gene_name=opt$gene,
    folder_of_plots=opt$folder
  )
  print("... finished.")
}
