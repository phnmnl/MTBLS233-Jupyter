#Parser

A tool to restructure the output files from OpenMS. This component is part of the MTBLS233-Jupyter use case and should be run after the TextExporter in OpenMS and follwed by the downstream-analysis notebook.

**Input:** A CSV file generated from the TextExporter in OpenMS

**Output:** A restructured CSV file with spectral features as rows and samples as columns


##Run Parser locally

Build your image, using the following command. Use the -t flag to tag it with any desired name.

```
$ docker build -t parser .
```
To run the service you need to provide it with the names of your input and output files and you need to add a data volume to your image containing your input file. In the example below the input data is located in the local directory *results* and a destination folder is created named data. 

```
$ docker run -v /home/MTBLS233-Jupyter/results:/data parser /data/input.csv /data/output.csv
```
