# MTBLS233 with PhenoMeNal Jupyter
OpenMS preprocessing, and R downstream analysis with Jupyter.

## Run MTBLS233 preprocessing workflow in Jupyter

Start by opening Jupyter in your browser at: `http://notebook.<deployment-id>.phenomenal.cloud/`.

### Ingest the MTBLS233 dataset from MetaboLights

[MetaboLights](http://www.ebi.ac.uk/metabolights/) offers an FTP service, so we can ingest the MTBLS233 dataset with Linux commands. 

1. First open a Jupyter terminal: `New > Terminal`
2. Ingest the dataset using **wget**:

```bash
wget ftp://anonymous@ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS233/*.mzML -
P MTBLS233/data/
```
