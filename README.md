# MTBLS233 with PhenoMeNal Jupyter
In this page we introduce an OpenMS preprocessing workflow, and R downstream analysis that you can run using the Jupyter fronted, that is provided by PhenoMeNal.

## Introduction
TBC @stephanieherman

## Run the preprocessing workflow

Start by opening Jupyter in your browser at: `http://notebook.<deployment-id>.phenomenal.cloud/`.

### Ingest the MTBLS233 dataset from MetaboLights

[MetaboLights](http://www.ebi.ac.uk/metabolights/) offers an FTP service, so we can ingest the MTBLS233 dataset with Linux commands.

1. First open a Jupyter terminal: `New > Terminal`
2. Ingest the dataset using **wget**:

```bash
wget ftp://anonymous@ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS233/*.mzML -P MTBLS233/data/
```

## Run the downstream analysis
TBC @stephanieherman
