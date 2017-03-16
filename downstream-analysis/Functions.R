print("The functions were succesfully loaded")

### Parse
Parse <- function(R) {
  R <- data.frame(lapply(R, as.character), stringsAsFactors=FALSE)
  #print(dim(R))
  
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


### Rename columns
renameColumns <- function(R) {
  #### Parameters ####
  renamePattern = c(
    "Blank_\\d+",
    "Pool_\\d+",
    "[CLH]\\d+_K\\d+"
  )
  ####
  
  #### Required packages ####
  library(stringr)
  ####
  
  df = R
  df <- data.frame(lapply(df, as.character), stringsAsFactors=FALSE)
  
  for (i in 1:length(colnames(df))) {
    for (j in 1:length(renamePattern)) {
      colname = str_match(colnames(df)[i], renamePattern[j])[1,1]
      #print(colname)
      if (!is.na(colname)) {
        #print(colname)
        colnames(df)[i] = colname
      }
    }
  }
  
  colnames(df) <- make.unique(colnames(df))
  return(df)
}


### Blank Filter
blankFilter <- function(R,blankFilterPassed) {
  ######## PARAMETER ########
  blankPattern = "Blank\\."
  samplePattern = "[CLH]\\d+\\.K\\d+"
  #blankFilterPassed = 0
  ###########################
  
  data = R
  data <- data.frame(lapply(data, as.character), stringsAsFactors=FALSE)
  
  #Compare every sample intensity with median blank intensity
  keepRow = apply(data, 1, function(row) {
    dataBlank = row[which(grepl(blankPattern, names(row)))]
    dataSamples = row[which(grepl(samplePattern, names(row)))]
    
    blankint = median(as.numeric(dataBlank), na.rm=TRUE)
    #print(paste("blankint",formatC(blankint, format="f", digits=0)))
    
    # Will this column pass the blank filter?
    columnPassed = sapply(dataSamples, function(sampleint) {
      sampleint = as.numeric(sampleint)
      #cat(paste("  sampleint",formatC(sampleint, format="f", digits=0)," "))
      
      if ((!is.na(blankint) & !is.na(sampleint) & sampleint*0.2 > blankint) | (is.na(blankint) & !is.na(sampleint))) {
        #print(paste((!is.na(blankint) & !is.na(sampleint) & sampleint*0.2 < blankint), (is.na(blankint) & !is.na(sampleint))," = TRUE"))
        return(TRUE)
      }
      else {
        #print("FALSE")
        return(FALSE)
      }
    })
    
    #print(paste("-->",sum(columnPassed)))
    if (sum(columnPassed) >= blankFilterPassed) {
      return(TRUE)
    }
    else {
      return(FALSE)
    }
  })
  cat(sum(keepRow), "number of features passed", "\n")
  df<-data[keepRow,]
  return(df)
}


### Consensus Map Normalization
consensusMapNormalization <- function(R, ignoreColsPattern, method, outlier, verbose) {
  ########## PARAMETERS #############
  #ignoreColsPattern = c("TCA", "Blank")
  #method = "mean"
  #outlier = c(0.68, 1/0.68)
  #verbose = TRUE
  ###################################
  
  df <- R
  df <- data.frame(lapply(df, as.character), stringsAsFactors=FALSE)
  
  if (verbose) {
      message("Maps: ")
      print(colnames(df))
  }
  
  ignoredCols = c()
  norm_cols_ind = c()
  num_features = c()
  norm_ratios = c()
  
  if (method != "mean" & method != "median") {
    error(paste("Illegal method:", method))
  }
  
  # Find map with most features
  for (i in 1:ncol(df)) {
    num_features = append(num_features, nrow(df[!is.na(df[,i]) & df[,i] > 0,]))
    
    if (colnames(df)[i] %in% c("mz", "mz_cf", "RT", "rt", "rt_cf", "id", "accession")) { ignoredCols = append(ignoredCols, colnames(df)[i]); next }
    
    if (length(ignoreColsPattern) > 0) {
      ignoreColsMatches = FALSE
      for (j in 1:length(ignoreColsPattern)) {
        if (grepl(ignoreColsPattern[j], colnames(df)[i], ignore.case=TRUE)) ignoreColsMatches = TRUE
      }
      if (ignoreColsMatches) { ignoredCols = append(ignoredCols, colnames(df)[i]); next }
    }
    
    norm_cols_ind = append(norm_cols_ind, i)
  }
  
  if (verbose) {
    message("Non-normalized columns: ")
    print(ignoredCols)
  }
  
  if (verbose) {
    message("Feature count:")
  }
  max_features = 0
  max_features_ind = 0
  for (i in 1:length(norm_cols_ind)) {
      if (verbose) {
          print(paste(colnames(df)[norm_cols_ind[i]], ": ", num_features[norm_cols_ind[i]], sep=""), quote=FALSE)
      }
    if (num_features[norm_cols_ind[i]] > max_features) {
      max_features = num_features[norm_cols_ind[i]]
      max_features_ind = norm_cols_ind[i]
    }
  }
  if (max_features == 0) error("Error: No features found.")
  
  if (verbose) {
    message("Most features:")
    print(paste(colnames(df)[max_features_ind], ": ", num_features[max_features_ind], sep=""), quote=FALSE)
  }
  
  # Get normalization ratio
  if (verbose) {
    message("Normalization ratios (map with most features / other map):")
    message(paste("Method: ", method, sep=""))
    message(paste("Outlier: ", format(outlier[1], digits=2), " < ratio < ", format(outlier[2], digits=2), sep=""))
  }
  for (i in 1:length(norm_cols_ind)) {
    ratios = as.numeric(df[,max_features_ind]) / as.numeric(df[,norm_cols_ind[i]])
    ratios = ratios[!is.na(ratios) & !is.infinite(ratios) & ratios > 0 & ratios > outlier[1] & ratios < outlier[2]]
    
    if (method == "mean") {
      m_ratio = mean(ratios, na.rm=TRUE)
    }
    else if (method == "median") {
      m_ratio = median(ratios, na.rm=TRUE)
    }
    if (verbose) {
        print(paste(colnames(df)[max_features_ind], " / ", colnames(df)[norm_cols_ind[i]], " = ", m_ratio, sep=""), quote=FALSE)    
    }
    norm_ratios = append(norm_ratios, m_ratio)
  }
  
  for (i in 1:length(norm_cols_ind)) {
    df[,norm_cols_ind[i]] = as.numeric(df[,norm_cols_ind[i]]) * norm_ratios[i]
  }
  
  return(list(df=df,ignoredCols=ignoredCols))
}


### Quality Assessment Filter
QAFilter <- function(R, poolFilterCount, biolReplFilterCount, numReplicates, maxRSD) {
  ####
  samplePattern = "[CLH]\\d+\\.K\\d+"
  poolPattern = "Pool\\."
  rsdPoolPattern = "Pool\\."
  
  #poolFilterCount = 5
  
  #biolReplFilterCount = 2
  #numReplicates = 3
  
  #maxRSD = 25
  ####
  
  df <- R
  df <- data.frame(lapply(df, as.character), stringsAsFactors=FALSE)
  
  filterBiolRepl = function(dataSamples) {
    conditions = c("C", "L", "H")
    timepoints = c("01", "03", "14")
    replicates = c("K1", "K2", "K3")
    sep = "\\."
    
    numReplicatesTrue = 0
    
    for (i in 1:length(conditions)) {
      for (j in 1:length(timepoints)) {
        values = 0
        for (k in 1:length(replicates)) {
          col = which(grepl(paste(conditions[i],timepoints[j],sep,replicates[k],sep=""), names(dataSamples)))
          
          if (length(col) == 0) {
            stop(paste("Error: ",conditions[i],timepoints[j],sep,replicates[k]," not found",sep=""))
          }
          else if (length(col) > 1) {
            stop(paste("Error: ",conditions[i],timepoints[j],sep,replicates[k]," found more than once:",sep=""))
            print(names(dataSamples)[col])
          }
          else {
            if (!is.na(dataSamples[col]) && dataSamples[col] > 0) {
              values = values + 1
            }					
          }
        }
        if (values >= numReplicates) {
          numReplicatesTrue = numReplicatesTrue + 1
        }
      }
    }
    
    return(numReplicatesTrue)
  }
  
  #Compare every sample intensity with median blank intensity
  keepRow = apply(df, 1, function(row) {
    dataSamples = row[which(grepl(samplePattern, names(row)))]
    dataPool = row[which(grepl(poolPattern, names(row)))]
    dataPoolRSD = row[which(grepl(rsdPoolPattern, names(row)))]
    
    pool = sum(!is.na(dataPool) & dataPool > 0)
    rsd = 100 * (sd(as.numeric(dataPoolRSD), na.rm=TRUE) / mean(as.numeric(dataPoolRSD), na.rm=TRUE))
    biolRepl = filterBiolRepl(dataSamples)
    
    if (pool >= poolFilterCount & rsd <= maxRSD & biolRepl >= biolReplFilterCount) {
      return(TRUE)
    }
    else {
      return(FALSE)
    }
  })
  
  df<-df[keepRow,]
  
  return(df)
}


### Missing Values
missingValues <- function(R) {
  df <- R
  df <- data.frame(lapply(df, as.character), stringsAsFactors=FALSE)
  
  conditions = c("C", "L", "H")
  cond.time.sep = ""
  timepoints = c("01", "03", "14")
  replicates = c("K1", "K2", "K3")
  
  for (condition in conditions) {
    for (timepoint in timepoints) {
      for (i in 1:nrow(df)) {
        col_ind = which(grepl(paste(condition, timepoint, sep=cond.time.sep), colnames(df)))
        missing = sum(is.na(df[i, col_ind]))
        if (missing == length(col_ind)) {
          df[i, col_ind] = 1
        }
      }
    }
  }
  return(df)
}


###Statistical Analysis
statisticalAnalysis <- function(R) {
  #####
  comparisons = list(
    C_L_01 = list(c("L01\\.K1", "L01\\.K2", "L01\\.K3"), c("C01\\.K1", "C01\\.K2", "C01\\.K3")),
    C_H_01 = list(c("H01\\.K1", "H01\\.K2", "H01\\.K3"), c("C01\\.K1", "C01\\.K2", "C01\\.K3")),
    C_L_03 = list(c("L03\\.K1", "L03\\.K2", "L03\\.K3"), c("C03\\.K1", "C03\\.K2", "C03\\.K3")),
    C_H_03 = list(c("H03\\.K1", "H03\\.K2", "H03\\.K3"), c("C03\\.K1", "C03\\.K2", "C03\\.K3")),
    C_L_14 = list(c("L14\\.K1", "L14\\.K2", "L14\\.K3"), c("C14\\.K1", "C14\\.K2", "C14\\.K3")),
    C_H_14 = list(c("H14\\.K1", "H14\\.K2", "H14\\.K3"), c("C14\\.K1", "C14\\.K2", "C14\\.K3")) 
  )
  #####
  
  df <- R
  df <- data.frame(lapply(df, as.character), stringsAsFactors=FALSE)
  
  
  fuzzyColMatch = function(colname, cnames) {
    res = which(grepl(colname, cnames))
    if (length(res) == 0) stop(paste("No matching column found for", colname))
    if (length(res) > 1) stop(paste("More than one matching column found for", colname))
    else res
  }
  
  
  for (i in 1:length(comparisons)) {
    name = names(comparisons)[i]
    
    indices1 = sapply(comparisons[[i]][[1]],function(x) fuzzyColMatch(x, colnames(df)))
    indices2 = sapply(comparisons[[i]][[2]],function(x) fuzzyColMatch(x, colnames(df)))
    
    df = cbind(df, apply(df, 1, function(x) tryCatch(t.test(as.numeric(x[indices1]), as.numeric(x[indices2]),var.equal=TRUE)$p.value, error=function(e) NA)))
    colnames(df)[length(colnames(df))] = paste(name,"_pval",sep="")
    
    df = cbind(df, apply(df, 1, function(x) tryCatch(mean(as.numeric(x[indices1]), na.rm=TRUE) / mean(as.numeric(x[indices2]), na.rm=TRUE), error=function(e) NA)))
    colnames(df)[length(colnames(df))] = paste(name,"_fc",sep="")
  }
  
  
  return(df)
}


### CSV Exporter