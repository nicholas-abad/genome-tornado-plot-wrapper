# dependencies.packages = c('ggplot2', 'data.table', 'devtools','grid', 'gridExtra','tiff',"shiny","shinydashboard","entropy")

# install.packages(dependencies.packages)

# if (!requireNamespace("BiocManager", quietly = TRUE))
# install.packages("BiocManager")

# BiocManager::install(c('GenomicRanges','quantsmooth','IRanges'))
# devtools::install()
library("optparse")

args = commandArgs(trailingOnly=TRUE)

option_list = list(
  make_option(c("-c", "--chromosome"), type="character", default=NULL,
              help="Chromosome", metavar="character"),
  make_option(c("-g", "--gene"), type="character", default=NULL,
              help="Gene", metavar="character"),
  make_option(c("-f", "--folder"), type="character", default="/omics/groups/OE0436/internal/nabad/GenomeTornadoPlot/PCAWG_plots_16Nov",
              help="Folder of Plots", metavar="character"),
  make_option(c("-s", "--saveplots"), type="character", default="/omics/groups/OE0436/internal/nabad/GenomeTornadoPlot/PCAWG_plots_16Nov",
              help="Decide to save plots or not.", metavar="character")
)

opt_parser = OptionParser(option_list=option_list)
opt = parse_args(opt_parser)

if (is.null(opt$chromosome) || is.null(opt$gene)){
  stop("Please specify both the chromosome and the gene.")
} else {
  print(paste("Chromosome: ", opt$chromosome))
  print(paste("Gene: ", opt$gene))
  print(paste("Output Folder: ", opt$folder))

  library(ggplot2)
  library(GenomeTornadoPlot)

  get_tornado_plot <- function(
    chromosome,
    gene_name,
    folder_of_plots
  ) {
    # Turn chromosome and gene_name to strings.
    chromosome <- paste(chromosome)
    gene_name <- paste(gene_name)

    # Load the dataset.
    path_to_rdata <- paste("/home/n795d/workspace/genome-tornado-plot-wrapper/GenomeTornadoPlot-files/chr", chromosome, ".Rdata", sep="")
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
      folder_of_plots, "/", gene_name, "_not_zoomed.png",
      sep=""
    )
    path_to_zoomed <- paste(
      folder_of_plots, "/", gene_name, "_zoomed.png",
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
