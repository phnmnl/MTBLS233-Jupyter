import luigi
from luigi.contrib.kubernetes import KubernetesJobTask
from os.path import basename
import glob
    
class PeakPickerTask(KubernetesJobTask):
    
    sampleFile = luigi.Parameter()
    paramFile = ""
    
    if sampleFile.find("_pos") != -1:
        paramFile = "PPparam_pos.ini"
    else:
        paramFile = "PPparam_neg.ini"
    
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
                    "-ini", "/work/openms-params/" + paramFile
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
    paramFile = ""
    
    if sampleFile.find("_pos") != -1:
        paramFile = "FFparam_pos.ini"
    else:
        paramFile = "FFparam_neg.ini"
    
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
                    "-ini", "/work/openms-params/" + paramFile
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
        return PeakPickerTask(sampleFile=self.sampleFile)
    
    def output(self):
        filename = basename("{0}.featureXML".format(*self.sampleFile.rsplit('.', 1)))
        return luigi.LocalTarget("results/"+filename)

class FeatureLinkerTask(KubernetesJobTask):
    
    groupSuffix = luigi.Parameter()
    
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
        inputFiles = glob.glob("data/*_"+self.groupSuffix+".mzML")
        return map(lambda f: FeatureFinderTask(sampleFile=f),inputFiles)
    
    def output(self):
        return luigi.LocalTarget("results/linked_"+self.groupSuffix+".consensusXML")

class FileFilterTask(KubernetesJobTask):
    
    groupSuffix = luigi.Parameter()
    
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
        return FeatureLinkerTask(groupSuffix=self.groupSuffix)
    
    def output(self):
        return luigi.LocalTarget("results/linked_filtered_"+self.groupSuffix+".consensusXML")
    
class TextExporterTask(KubernetesJobTask):
    
    groupSuffix = luigi.Parameter()
    
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
        return FileFilterTask(groupSuffix=self.groupSuffix)
    
    def output(self):
        return luigi.LocalTarget("results/"+self.groupSuffix+".csv")

class AllGroups(luigi.WrapperTask):
    def requires(self):
#        yield TextExporterTask(groupSuffix="alternate_neg_high_mr")
#        yield TextExporterTask(groupSuffix="alternate_neg_low_mr")
#        yield TextExporterTask(groupSuffix="alternate_neg")
        yield TextExporterTask(groupSuffix="alternate_pos_high_mr")
        yield TextExporterTask(groupSuffix="alternate_pos_low_mr")
#        yield TextExporterTask(groupSuffix="alternate_pos")
#        yield TextExporterTask(groupSuffix="ges_neg")
#        yield TextExporterTask(groupSuffix="ges_pos")
#        yield TextExporterTask(groupSuffix="high_neg")
#        yield TextExporterTask(groupSuffix="high_pos")
#        yield TextExporterTask(groupSuffix="low_neg")
#        yield TextExporterTask(groupSuffix="low_pos")
        
