
import threading
import model_params     
import time

from nupic.frameworks.opf.modelfactory             import ModelFactory # to create the nupic model
from nupic.algorithms.anomaly_likelihood           import AnomalyLikelihood

class NupicModels(threading.Thread):
    """
    NuPIC models - One instance created per frequency bin to analise in this project
    """
    
    def __init__(self, number, HTMHERTZ, verbose):

        threading.Thread.__init__(self)
        self.daemon = True

        self.verbose    = verbose

        # Flags and logic 
        self.HTM        = 1
        self.HTMHERTZ   = HTMHERTZ
        self.number     = number

        # Create model, set the predicted field, run and get anomaly
        self.amplitude  = 1
        self.model      = ModelFactory.create(model_params.MODEL_PARAMS)
        self.model.enableInference({'predictedField': 'binAmplitude'})
        self.likelihoods= AnomalyLikelihood()

        self.result     = self.model.run({"binAmplitude" : 0})
        self.anomaly    = self.result.inferences['anomalyScore']    
        self.likelihood = self.likelihoods.anomalyProbability(0, 0) 

    
    def run(self): 
        self.startTime = time.time()
        
        while self.HTM:
            """ Continuous Execution""" 
            if time.time()-self.startTime > 1/self.HTMHERTZ:
                self.result     = self.model.run({"binAmplitude" : self.amplitude})
                self.anomaly    = self.result.inferences['anomalyScore']    
                self.likelihood = self.likelihoods.anomalyProbability(self.amplitude, self.anomaly) 
                if self.verbose:
                    print 'Anomaly Thread '    + str(self.number) + ": " + str(self.anomaly)
                    print 'Time taken Thread ' + str(self.number) + ': ' + format(time.time() - self.startTime)           
                self.startTime = time.time()

        self.HTM = 0
        print"End of Nupic Model " + str(self.number)
