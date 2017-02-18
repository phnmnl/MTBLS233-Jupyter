import luigi
from luigi.contrib.kubernetes import KubernetesJobTask
from os.path import basename
import glob
    
class PeakPickerTask(KubernetesJobTask):
    
    sampleFile = luigi.Parameter()
    
    name = "peak-picker"
    max_retrials = 3
    
    @property
    def spec_schema(self): 
        return {
            "containers": [{
                "name": self.name,
                "image": "docker-registry.phenomenal-h2020.eu/phnmnl/openms",
                "command": [
                    "PeakPickerHiRes",
                    "-in", "/work/" + self.sampleFile,
                    "-out", "/work/" + self.output().path,
                    "-ini", "/work/openms-params/PPparam.ini"
                ],
                "volumeMounts": [{
                    "mountPath": "/work",
                    "name": "shared-volume",
                    "subPath": "MTBLS233"
                 }]
             }],
             "volumes": [{
                 "name": "shared-volume",
                 "persistentVolumeClaim": {
                     "claimName": "jupyter-volume-claim"
                 }
             }]
        }
    
    def output(self):
        filename = basename("{0}_{2}.{1}".format(*self.sampleFile.rsplit('.', 1) + ["peaks"]))
        return luigi.LocalTarget("results/"+filename)
    
class FeatureFinderTask(KubernetesJobTask):
    
    sampleFile = luigi.Parameter()
    
    name = "feature-finder"
    max_retrials = 3
    
    @property
    def spec_schema(self): 
        return {
            "containers": [{
                "name": self.name,
                "image": "docker-registry.phenomenal-h2020.eu/phnmnl/openms",
                "command": [
                    "FeatureFinderMetabo",
                    "-in", "/work/" + self.input().path,
                    "-out", "/work/" + self.output().path,
                    "-ini", "/work/openms-params/FFparam.ini"
                ],
                "volumeMounts": [{
                    "mountPath": "/work",
                    "name": "shared-volume",
                    "subPath": "MTBLS233"
                 }]
             }],
             "volumes": [{
                 "name": "shared-volume",
                 "persistentVolumeClaim": {
                     "claimName": "jupyter-volume-claim"
                 }
             }]
        }
    
    def requires(self):
        return PeakPickerTask(sampleFile=self.sampleFile)
    
    def output(self):
        filename = basename("{0}.featureXML".format(*self.sampleFile.rsplit('.', 1)))
        return luigi.LocalTarget("results/"+filename)

class FeatureLinkerTask(KubernetesJobTask):
    
    name = "feature-linker"
    max_retrials = 3
    
    @property
    def spec_schema(self): 
        inputList = map(lambda i: "/work/" + i.path, self.input())
        inputStr = ' '.join(inputList)
        return {
            "containers": [{
                "name": self.name,
                "image": "docker-registry.phenomenal-h2020.eu/phnmnl/openms",
                "command": ["sh","-c"],
                "args": [
                    "FeatureLinkerUnlabeledQT -in " + inputStr +
                    " -out /work/" + self.output().path +
                    " -ini /work/openms-params/FLparam.ini"
                ],
                "volumeMounts": [{
                    "mountPath": "/work",
                    "name": "shared-volume",
                    "subPath": "MTBLS233"
                 }]
             }],
             "volumes": [{
                 "name": "shared-volume",
                 "persistentVolumeClaim": {
                     "claimName": "jupyter-volume-claim"
                 }
             }]
        }
    
    def requires(self):
        inputFiles = glob.glob("data/*.mzML")
        return map(lambda f: FeatureFinderTask(sampleFile=f),inputFiles)
    
    def output(self):
        return luigi.LocalTarget("results/linked.consensusXML")

class FileFilterTask(KubernetesJobTask):
    
    name = "file-filter"
    max_retrials = 3
    
    @property
    def spec_schema(self): 
        return {
            "containers": [{
                "name": self.name,
                "image": "docker-registry.phenomenal-h2020.eu/phnmnl/openms",
                "command": [
                    "FileFilter",
                    "-in", "/work/" + self.input().path,
                    "-out", "/work/" + self.output().path,
                    "-ini", "/work/openms-params/FileFparam.ini"
                ],
                "volumeMounts": [{
                    "mountPath": "/work",
                    "name": "shared-volume",
                    "subPath": "MTBLS233"
                 }]
             }],
             "volumes": [{
                 "name": "shared-volume",
                 "persistentVolumeClaim": {
                     "claimName": "jupyter-volume-claim"
                 }
             }]
        }
    
    def requires(self):
        return FeatureLinkerTask()
    
    def output(self):
        return luigi.LocalTarget("results/linked_filtered.consensusXML")
    
class TextExporterTask(KubernetesJobTask):
    
    name = "text-exporter"
    max_retrials = 3
    
    @property
    def spec_schema(self): 
        return {
            "containers": [{
                "name": self.name,
                "image": "docker-registry.phenomenal-h2020.eu/phnmnl/openms",
                "command": [
                    "TextExporter",
                    "-in", "/work/" + self.input().path,
                    "-out", "/work/" + self.output().path,
                    "-ini", "/work/openms-params/TEparam.ini"
                ],
                "volumeMounts": [{
                    "mountPath": "/work",
                    "name": "shared-volume",
                    "subPath": "MTBLS233"
                 }]
             }],
             "volumes": [{
                 "name": "shared-volume",
                 "persistentVolumeClaim": {
                     "claimName": "jupyter-volume-claim"
                 }
             }]
        }
    
    def requires(self):
        return FeatureLinkerTask()
    
    def output(self):
        return luigi.LocalTarget("results/exported.csv")
    