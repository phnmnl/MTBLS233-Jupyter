import luigi
from luigi.contrib.kubernetes import KubernetesJobTask
from os.path import basename
import glob
    
class PeakPickerTask(KubernetesJobTask):
    
    sampleFile = luigi.Parameter()
    posOrNeg = luigi.Parameter()
    endSuffix = luigi.Parameter()  
    paramFile = "PPparam"
        
    name = "peak-picker"
    max_retrials = 3
    
    @property
    def spec_schema(self): 
        return {
            "containers": [{
                "name": self.name,
                "image": "container-registry.phenomenal-h2020.eu/phnmnl/openms:v1.11.1_cv0.1.9",
                "command": [
                    "PeakPickerHiRes",
                    "-in", "/work/" + self.sampleFile,
                    "-out", "/work/" + self.output().path,
                    "-ini", "/work/openms-params/" + self.paramFile + self.posOrNeg + ".ini"
                ],
                "resources": {
                  "requests": {
                    "memory": "2G",
                    "cpu": "1"
                  }
                },
                "volumeMounts": [{
                    "mountPath": "/work",
                    "name": "shared-volume",
                    "subPath": "jupyter/MTBLS233"
                 }]
             }],
             "volumes": [{
                 "name": "shared-volume",
                 "persistentVolumeClaim": {
                     "claimName": "galaxy-pvc"
                 }
             }]
        }
    
    def output(self):
        filename = basename("{0}_{2}.{1}".format(*self.sampleFile.rsplit('.', 1) + ["peaks"]))
        return luigi.LocalTarget("results/"+filename)
    
class FeatureFinderTask(KubernetesJobTask):
    
    sampleFile = luigi.Parameter()
    posOrNeg = luigi.Parameter()
    endSuffix = luigi.Parameter()  
    paramFile = "FFparam"

    name = "feature-finder"
    max_retrials = 3
    
    @property
    def spec_schema(self): 
        return {
            "containers": [{
                "name": self.name,
                "image": "container-registry.phenomenal-h2020.eu/phnmnl/openms:v1.11.1_cv0.1.9",
                "command": [
                    "FeatureFinderMetabo",
                    "-in", "/work/" + self.input().path,
                    "-out", "/work/" + self.output().path,
                    "-ini", "/work/openms-params/" + self.paramFile + self.posOrNeg + ".ini" 
                ],
                "resources": {
                  "requests": {
                    "memory": "2G",
                    "cpu": "1"
                  }
                },
                "volumeMounts": [{
                    "mountPath": "/work",
                    "name": "shared-volume",
                    "subPath": "jupyter/MTBLS233"
                 }]
             }],
             "volumes": [{
                 "name": "shared-volume",
                 "persistentVolumeClaim": {
                     "claimName": "galaxy-pvc"
                 }
             }]
        }
    
    def requires(self):
        return PeakPickerTask(sampleFile=self.sampleFile, posOrNeg=self.posOrNeg, endSuffix=self.endSuffix)
    
    def output(self):
        filename = basename("{0}.featureXML".format(*self.sampleFile.rsplit('.', 1)))
        return luigi.LocalTarget("results/"+filename)

class FeatureLinkerTask(KubernetesJobTask):
    
    groupSuffix = luigi.Parameter()
    posOrNeg = luigi.Parameter()
    endSuffix = luigi.Parameter()
 
    name = "feature-linker"
    max_retrials = 3
    
    @property
    def spec_schema(self): 
        inputList = map(lambda i: "/work/" + i.path, self.input())
        inputStr = ' '.join(inputList)
        return {
            "containers": [{
                "name": self.name,
                "image": "container-registry.phenomenal-h2020.eu/phnmnl/openms:v1.11.1_cv0.1.9",
                "command": ["sh","-c"],
                "args": [
                    "FeatureLinkerUnlabeledQT -in " + inputStr +
                    " -out /work/" + self.output().path +
                    " -ini /work/openms-params/FLparam.ini" +
                    " -threads 2"
                ],
                "resources": {
                  "requests": {
                    "memory": "4G",
                    "cpu": "2"
                  }
                },
                "volumeMounts": [{
                    "mountPath": "/work",
                    "name": "shared-volume",
                    "subPath": "jupyter/MTBLS233"
                 }]
             }],
             "volumes": [{
                 "name": "shared-volume",
                 "persistentVolumeClaim": {
                     "claimName": "galaxy-pvc"
                 }
             }]
        }
    
    def requires(self):
        inputFiles = glob.glob("data/*_"+self.groupSuffix+self.posOrNeg+self.endSuffix+".mzML")
        return map(lambda f: FeatureFinderTask(sampleFile=f, posOrNeg=self.posOrNeg, endSuffix=self.endSuffix),inputFiles)
    
    def output(self):
        return luigi.LocalTarget("results/linked_"+self.groupSuffix+self.posOrNeg+self.endSuffix+".consensusXML")

class FileFilterTask(KubernetesJobTask):
    
    groupSuffix = luigi.Parameter()
    posOrNeg = luigi.Parameter()
    endSuffix = luigi.Parameter()
    
    name = "file-filter"
    max_retrials = 3
    
    @property
    def spec_schema(self): 
        return {
            "containers": [{
                "name": self.name,
                "image": "container-registry.phenomenal-h2020.eu/phnmnl/openms:v1.11.1_cv0.1.9",
                "command": [
                    "FileFilter",
                    "-in", "/work/" + self.input().path,
                    "-out", "/work/" + self.output().path,
                    "-ini", "/work/openms-params/FileFparam.ini"
                ],
                "resources": {
                  "requests": {
                    "memory": "2G",
                    "cpu": "1"
                  }
                },
                "volumeMounts": [{
                    "mountPath": "/work",
                    "name": "shared-volume",
                    "subPath": "jupyter/MTBLS233"
                 }]
             }],
             "volumes": [{
                 "name": "shared-volume",
                 "persistentVolumeClaim": {
                     "claimName": "galaxy-pvc"
                 }
             }]
        }
    
    def requires(self):
        return FeatureLinkerTask(groupSuffix=self.groupSuffix, posOrNeg=self.posOrNeg, endSuffix=self.endSuffix)
    
    def output(self):
        return luigi.LocalTarget("results/linked_filtered_"+self.groupSuffix+self.posOrNeg+self.endSuffix+".consensusXML")
    
class TextExporterTask(KubernetesJobTask):
    
    groupSuffix = luigi.Parameter()
    posOrNeg = luigi.Parameter()
    endSuffix = luigi.Parameter()
    
    name = "text-exporter"
    max_retrials = 3
    
    @property
    def spec_schema(self): 
        return {
            "containers": [{
                "name": self.name,
                "image": "container-registry.phenomenal-h2020.eu/phnmnl/openms:v1.11.1_cv0.1.9",
                "command": [
                    "TextExporter",
                    "-in", "/work/" + self.input().path,
                    "-out", "/work/" + self.output().path,
                    "-ini", "/work/openms-params/TEparam.ini"
                ],
                "resources": {
                  "requests": {
                    "memory": "2G",
                    "cpu": "1"
                  }
                },
                "volumeMounts": [{
                    "mountPath": "/work",
                    "name": "shared-volume",
                    "subPath": "jupyter/MTBLS233"
                 }]
             }],
             "volumes": [{
                 "name": "shared-volume",
                 "persistentVolumeClaim": {
                     "claimName": "galaxy-pvc"
                 }
             }]
        }
    
    def requires(self):
        return FileFilterTask(groupSuffix=self.groupSuffix, posOrNeg=self.posOrNeg, endSuffix=self.endSuffix)
    
    def output(self):
        return luigi.LocalTarget("results/"+self.groupSuffix+self.posOrNeg+self.endSuffix+".csv")

class AllGroups(luigi.WrapperTask):
    def requires(self): 
        yield TextExporterTask(groupSuffix="alternate", posOrNeg="_neg", endSuffix="_high_mr")
        yield TextExporterTask(groupSuffix="alternate", posOrNeg="_pos", endSuffix="_high_mr")
        yield TextExporterTask(groupSuffix="alternate", posOrNeg="_neg", endSuffix="_low_mr")
        yield TextExporterTask(groupSuffix="alternate", posOrNeg="_pos", endSuffix="_low_mr")
        yield TextExporterTask(groupSuffix="alternate", posOrNeg="_neg", endSuffix="")
        yield TextExporterTask(groupSuffix="alternate", posOrNeg="_pos", endSuffix="")
        yield TextExporterTask(groupSuffix="ges", posOrNeg="_neg", endSuffix="")
        yield TextExporterTask(groupSuffix="ges", posOrNeg="_pos", endSuffix="")
        yield TextExporterTask(groupSuffix="high", posOrNeg="_neg", endSuffix="")
        yield TextExporterTask(groupSuffix="high", posOrNeg="_pos", endSuffix="")
        yield TextExporterTask(groupSuffix="low", posOrNeg="_neg", endSuffix="")
        yield TextExporterTask(groupSuffix="low", posOrNeg="_pos", endSuffix="")
