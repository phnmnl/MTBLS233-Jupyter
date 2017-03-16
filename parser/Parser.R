install.packages("R.utils")
library(R.utils)
args <- commandArgs(trailingOnly = TRUE)

input = args[1]
output = args[2]

Parse <- function(R) {
  R <- data.frame(lapply(R, as.character), stringsAsFactors=FALSE)
  
  map = list()
  dflist = list()
  cons = FALSE
  count = -1
  
  for (i in 1:nrow(R)) {
    line = as.character(R[i,])
    
    if (line[1] == "MAP") {
      map[as.numeric(line[2]) + 1] = basename(line[3])
    }
    
    if (line[1] == "#CONSENSUS") {
      col_names_line = line
    }
    
    if (line[1] == "CONSENSUS") {
      cons = TRUE
      count = (length(line) - 7) / 5
      if ((length(line) - 7) %% 5 != 0) print("Warning: mod error")
      
      row = data.frame(matrix(nrow=1, ncol=0))
      
      row$mz_cf = line[3]			
      row$rt_cf = line[2]
      
      for (j in 1:count) {
        row[[paste("int_",j,sep="")]] = line[5 + j*5]
      }
      
      dflist[[length(dflist) + 1]] = row
    }
  }
  
  col_names = c("mz", "rt")
  for (i in 1:count) {
    col_names = c(col_names, map[[i]])
  }
  
  df = do.call(rbind, dflist)
  
  colnames(df) = col_names
  df = df[order(as.numeric(df$mz)), ]
  
  return(df)
}

nL <- countLines(input)
nL = read.csv(input, 
              skip=nL-1,
              fill=TRUE,
              sep="")
file = read.csv(input, 
                header = FALSE, comment.char="#",
                stringsAsFactors = FALSE, 
                fill=TRUE, 
                col.names= paste0("V",seq_len(length(nL))), 
                sep="")

parsed <- Parse(file)
parsed[parsed=="NaN"] <- NA

write.csv(parsed,file=output,row.names=F)
