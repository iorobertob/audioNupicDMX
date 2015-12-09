
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
#
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
import threading
import time

import ModelParams 
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
        self.model      = ModelFactory.create(ModelParams.MODEL_PARAMS)
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
