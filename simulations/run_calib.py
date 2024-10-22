import os
import sys
import shutil
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from gpytorch.constraints import GreaterThan
sys.path.append("../")
from calibration_common.batch_generators.turbo_thompson_sampling import TurboThompsonSampling 
from calibration_common.emulators.GP import ExactGP   
from calibration_common.bo import BO 
from calibration_common.plot import * 
from my_func import my_func as myFunc 
from compare_to_data.run_full_comparison import plot_prevalence,plot_incidence,compute_scores_across_site,save_maxEIR,save_AnnualIncidence 
from clean_all import clean_analyzers, clean_logs
from translate_parameters import translate_parameters

import manifest as manifest

# Experiment details
Site="Dummy"
exp_label = "241008_perennial"
output_dir = f"output/{exp_label}"
best_dir = f"output/{exp_label}" 

calib_coord = pd.read_csv(os.path.join(manifest.input_files_path,"calibration_coordinator.csv"))

# Botorch details
calib_coord = calib_coord.set_index("site")
init_samples=int(calib_coord.at[Site,"init_size"])
init_batches =  int(calib_coord.at[Site,"init_batches"]) #1 
emulator_batch_size = int(calib_coord.at[Site, 'batch_size'])
gp_max_eval = int(calib_coord.at[Site, 'max_eval'])
failure_limit = int(calib_coord.at[Site, 'failure_limit'])

param_key=pd.read_csv("test_parameter_key.csv")

# Define the Problem, it must be a functor
class Problem:
    def __init__(self,workdir="checkpoints/emod"):
        self.dim = int(param_key.shape[0])  #4 # mandatory dimension
        self.ymax = None #max value
        self.best = None
        self.n = 0
        self.workdir = workdir
        
        try:
            self.ymax = np.loadtxt(f"{self.workdir}/emod.ymax.txt").astype(float)
            self.n = np.loadtxt(f"{self.workdir}/emod.n.txt").astype(int)
        except IOError:
            self.ymax = None
            self.n = 0
        os.makedirs(os.path.relpath(f'{self.workdir}/'), exist_ok=True)

    # The input is a vector that contains multiple set of parameters to be evaluated
    def __call__(self, X):
        
        
        wdir=os.path.join(f"{self.workdir}/LF_{self.n}")
        os.makedirs(wdir,exist_ok=True)
            
        # logic for continuing a "stuck" round which has simulation_output but was not scored
        # if(self.n==0):
        #     Y0 = compute_scores_across_site("Nanoro")
        #     X = pd.read_csv(os.path.join(f"{self.workdir}/LF_{self.n}/translated_params.csv"))
        #     X = [numpy(x) for x in X["unit_value"]]
        #     X= [X[i:i+16] for i in range(0, len(X), 16)]
        #     print(X)
        # else:
        #     Y0=myFunc(X,wdir)
        Y0=myFunc(X,wdir)
        Y1 = pd.melt(Y0, id_vars="param_set")
        Y1 = Y1.groupby("param_set")['value'].agg('sum').reset_index(name='score')
        print("Final Summary Scores")
        print(Y1.to_string())    
        
        params=Y1['param_set']
        Y=Y1['score']*-1.0
        xc = []
        yc = []
        pc = []
        for j in range(len(Y)):
            if pd.isna(Y[j]):
                continue
            else:
                xc.append(X[j].tolist())
                yc.append([Y[j]])
                pc.append(params[j])
        xc2=[tuple(i) for i in xc]
        links=dict(zip(xc2,yc)) 
        pset=dict(zip(pc,yc))

        # If new best value is found, save it and some other data
        if self.ymax is None:
            self.ymax = max(links.values())
            best_x = max(links,key=links.get)
            best_p = max(pset,key=pset.get)
            self.best = translate_parameters(param_key,best_x,best_p)
            os.makedirs(os.path.join(f"{self.workdir}/LF_{self.n}"),exist_ok=True)
            np.savetxt(f"{self.workdir}/emod.ymax.txt", self.ymax)
            np.savetxt(f"{self.workdir}/LF_{self.n}/emod.ymax.txt", self.ymax)
            self.best.to_csv(f"{self.workdir}/LF_{self.n}/emod.best.csv")
            Y0['round'] = [self.n] * len(Y0)
            Y0.to_csv(f"{self.workdir}/all_scores.csv")
            mEIR = save_maxEIR(site=Site, wdir = f"{self.workdir}/LF_{self.n}")
            mEIR.to_csv(f"{self.workdir}/LF_{self.n}/EIR_range.csv")
            ACI = save_AnnualIncidence(site=Site, wdir =f"{self.workdir}/LF_{self.n}")
            ACI.to_csv(f"{self.workdir}/LF_{self.n}/ACI.csv")
            plot_prevalence(site=Site, plt_dir=os.path.join(f"{self.workdir}/LF_{self.n}"), wdir=os.path.join(f"{self.workdir}/LF_{self.n}"))
            plot_incidence(site=Site, plt_dir=os.path.join(f"{self.workdir}/LF_{self.n}"), wdir=os.path.join(f"{self.workdir}/LF_{self.n}"))
            shutil.copytree(f"{manifest.simulation_output_filepath}",f"{self.workdir}/LF_{self.n}/SO")
            self.n += 1
            np.savetxt(f"{self.workdir}/emod.n.txt", [self.n])
            clean_analyzers()
	    clean_logs()
            
        else:
            os.makedirs(os.path.join(f"{self.workdir}/LF_{self.n}"),exist_ok=True)
            # Only create plots or update emod.best and emod.ymax if fit improves
            if max(links.values())[0] > self.ymax:
                self.ymax = max(links.values()) #weighted_lf
                best_x = max(links,key=links.get)
                best_p = max(pset,key=pset.get)
                self.best = translate_parameters(param_key,best_x,best_p)
                self.best.to_csv(f"{self.workdir}/LF_{self.n}/emod.best.csv")
                mEIR = save_maxEIR(site=Site, wdir = f"{self.workdir}/LF_{self.n}")
                mEIR.to_csv(f"{self.workdir}/LF_{self.n}/EIR_range.csv")
                ACI = save_AnnualIncidence(site=Site, wdir =f"{self.workdir}/LF_{self.n}")
                ACI.to_csv(f"{self.workdir}/LF_{self.n}/ACI.csv")
                plot_prevalence(site=Site, plt_dir=os.path.join(f"{self.workdir}/LF_{self.n}"), wdir=os.path.join(f"{self.workdir}/LF_{self.n}"))
                plot_incidence(site=Site, plt_dir=os.path.join(f"{self.workdir}/LF_{self.n}"), wdir=os.path.join(f"{self.workdir}/LF_{self.n}"))
                np.savetxt(f"{self.workdir}/emod.ymax.txt", [self.ymax])
                np.savetxt(f"{self.workdir}/LF_{self.n}/emod.ymax.txt", [self.ymax])
            Y0['round'] = [self.n] * len(Y0)
            score_df=pd.read_csv(f"{self.workdir}/all_scores.csv")
            score_df=pd.concat([score_df,Y0])
            score_df.to_csv(f"{self.workdir}/all_scores.csv")
            shutil.copytree(f"{manifest.simulation_output_filepath}",f"{self.workdir}/LF_{self.n}/SO")
            self.n += 1
            np.savetxt(f"{self.workdir}/emod.n.txt", [self.n])
            clean_analyzers()
	    clean_logs()            
        return torch.tensor(xc,dtype=torch.float64), torch.tensor(yc)


problem = Problem(workdir=f"output/{exp_label}")

# Delete everything and restart from scratch 
# Comment this line to restart from the last state instead
# if os.path.exists(output_dir): 
#     shutil.rmtree(output_dir)
# if os.path.exists(best_dir): 
#     shutil.rmtree(best_dir)

# at beginning of workflow, cleanup all sbatch scripts for analysis
clean_analyzers()
clean_logs()
# Create the GP model
# See emulators/GP.py for a list of GP models
# Or add your own, see: https://botorch.org/docs/models
model = ExactGP(noise_constraint=GreaterThan(1e-6))

# Create batch generator(s)
tts = TurboThompsonSampling(batch_size=emulator_batch_size, failure_tolerance=failure_limit, dim=problem.dim) #64

# Create the workflow
bo = BO(problem=problem, model=model, batch_generator=batch_generator, checkpointdir=output_dir, max_evaluations=gp_max_eval)

# Sample and evaluate sets of parameters randomly drawn from the unit cube
#bo.initRandom(2)

bo.initRandom(init_samples, n_batches = init_batches)

# Run the optimization loop
bo.run(exp_label=f"{exp_label}")


