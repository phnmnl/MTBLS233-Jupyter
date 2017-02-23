# MTBLS233 with PhenoMeNal Jupyter
In this page we introduce an OpenMS preprocessing workflow, and R downstream analysis that you can run using the Jupyter fronted, that is provided by PhenoMeNal.

## Introduction
TBC @stephanieherman

## Run the preprocessing workflow

Start by opening Jupyter in your browser at: 

`http://notebook.<deployment-id>.phenomenal.cloud/`

### Ingest the MTBLS233 dataset from MetaboLights

[MetaboLights](http://www.ebi.ac.uk/metabolights/) offers an FTP service, so we can ingest the MTBLS233 dataset with Linux commands. 

1. First open a Jupyter terminal: `New > Terminal`
2. Ingest the dataset using **wget**:

```bash
wget ftp://anonymous@ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS233/*.mzML -P MTBLS233/data/
```

### Run the preprocessing workflow with Luigi

In order to run the preprocessing analysis we use the [Luigi](https://github.com/spotify/luigi) wrokflow system. Please notice that this is a heavy analysis, and to run it successfully you will have to deploy a moderately large number of fat nodes in your cloud provider. To run the preprocessing workflow please run:

```bash
cd MTBLS233 
export PYTHONPATH=./ 
luigi --module preprocessing_workflow AllGroups \
  --scheduler-host luigi.default \
  --workers 40
```

If everithing goes well you'll be able to monitor the progress of your analysis at:

`http://luigi.<deployment-id>.phenomenal.cloud/`

## Run the downstream analysis
TBC @stephanieherman
