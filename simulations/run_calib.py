##### Import required packages #####
# standard packages
import os
import sys
import shutil
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import torch
from gpytorch.constraints import GreaterThan
# from local directory
import manifest as manifest
sys.path.append("../calibration_common")
# from calibration_common
from batch_generators.turbo_thompson_sampling import TurboThompsonSampling 
from emulators.GP import ExactGP   
from bo import BO 
from post_calibration_analysis import post_calibration_analysis
# from environment_calibration_common
sys.path.append("../environment_calibration_common")
from clean_all import clean_analyzers, clean_logs, clean_COMPS_ID
from translate_parameters import translate_parameters
from helpers import load_coordinator_df
from my_func import my_func as myFunc
sys.path.append("../environment_calibration_common/compare_to_data")
from run_full_comparison import plot_allAge_prevalence,plot_incidence,compute_scores_across_site,save_rangeEIR,save_AnnualIncidence,plot_pfpr_microscopy 


####################################
# Experiment details - this is the only section you need to edit with the script
Site=manifest.SITE
exp_label = manifest.EXPERIMENT_LABEL
####################################

output_dir = f"output/{exp_label}"
best_dir = f"output/{exp_label}" 

calib_coord = pd.read_csv(manifest.calibration_coordinator_path)

# Botorch details
calib_coord = calib_coord.set_index("site")
init_samples=int(calib_coord.at[Site,"init_size"])
init_batches =  int(calib_coord.at[Site,"init_batches"])  
emulator_batch_size = int(calib_coord.at[Site, 'batch_size'])
gp_max_eval = int(calib_coord.at[Site, 'max_eval'])
failure_limit = int(calib_coord.at[Site, 'failure_limit'])
success_limit = int(calib_coord.at[Site,'success_limit'])

param_key=pd.read_csv("parameter_key.csv")

coord_df=load_coordinator_df()
incidence_agebin=float(coord_df.at['incidence_comparison_agebin','value'])
prevalence_agebin=float(coord_df.at['prevalence_comparison_agebin','value'])

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
            
        Y0=myFunc(X,wdir)
        # Clean up any non-score columns returned by myfunc
        ps = Y0['param_set']
        Y0 = Y0.filter(like='_score')
        Y0['param_set']=ps
        # Get sum of scores per param set
        Y1 = pd.melt(Y0, id_vars="param_set")
        Y1 = Y1.groupby("param_set")['value'].agg('sum').reset_index(name='score')
        params=Y1['param_set']
        # Negate score (for maximimzing)
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
            Y0.to_csv(f"{self.workdir}/all_LL.csv")
            mEIR = save_rangeEIR(site=Site, wdir = f"{self.workdir}/LF_{self.n}")
            mEIR.to_csv(f"{self.workdir}/LF_{self.n}/EIR_range.csv")
           
            if(coord_df.at["incidence_comparison","value"]):
                ACI = save_AnnualIncidence(site=Site,agebin=incidence_agebin, 
                                           wdir =f"{self.workdir}/LF_{self.n}")
                ACI.to_csv(f"{self.workdir}/LF_{self.n}/ACI.csv")
                plot_incidence(site=Site, agebin=incidence_agebin,
                               plt_dir=os.path.join(f"{self.workdir}/LF_{self.n}"), 
                               wdir=os.path.join(f"{self.workdir}/LF_{self.n}"))
            if(coord_df.at["prevalence_comparison","value"]):
                if(coord_df.at["prevalence_comparison_diagnostic","value"]=="PCR"):
                    plot_allAge_prevalence(site=Site, 
                                           plt_dir=os.path.join(f"{self.workdir}/LF_{self.n}"), 
                                           wdir=os.path.join(f"{self.workdir}/LF_{self.n}"))
                if(coord_df.at["prevalence_comparison_diagnostic","value"]=="Microscopy"):
                    plot_pfpr_microscopy(site=Site,
                                         plt_dir=os.path.join(f"{self.workdir}/LF_{self.n}"),
                                         wdir=os.path.join(f"{self.workdir}/LF_{self.n}"),
                                         agebin=prevalence_agebin)
            shutil.copytree(f"{manifest.simulation_output_filepath}",f"{self.workdir}/LF_{self.n}/SO")
            self.n += 1
            np.savetxt(f"{self.workdir}/emod.n.txt", [self.n])
            clean_analyzers()
            #clean_logs()
            clean_COMPS_ID()
        else:
            os.makedirs(os.path.join(f"{self.workdir}/LF_{self.n}"),exist_ok=True)
            # Only create plots or update emod.best and emod.ymax if fit improves
            if max(links.values())[0] > self.ymax:
                self.ymax = max(links.values()) #weighted_lf
                best_x = max(links,key=links.get)
                best_p = max(pset,key=pset.get)
                self.best = translate_parameters(param_key,best_x,best_p)
                self.best.to_csv(f"{self.workdir}/LF_{self.n}/emod.best.csv")
                mEIR = save_rangeEIR(site=Site, wdir = f"{self.workdir}/LF_{self.n}")
                mEIR.to_csv(f"{self.workdir}/LF_{self.n}/EIR_range.csv")
               
                if(coord_df.at["incidence_comparison","value"]):
                    ACI = save_AnnualIncidence(site=Site,agebin=incidence_agebin, 
                                               wdir =f"{self.workdir}/LF_{self.n}")
                    ACI.to_csv(f"{self.workdir}/LF_{self.n}/ACI.csv")
                    plot_incidence(site=Site, agebin=incidence_agebin,
                                   plt_dir=os.path.join(f"{self.workdir}/LF_{self.n}"), 
                                   wdir=os.path.join(f"{self.workdir}/LF_{self.n}"))
                if(coord_df.at["prevalence_comparison","value"]):
                    if(coord_df.at["prevalence_comparison_diagnostic","value"]=="PCR"):
                        plot_allAge_prevalence(site=Site, 
                                               plt_dir=os.path.join(f"{self.workdir}/LF_{self.n}"), 
                                               wdir=os.path.join(f"{self.workdir}/LF_{self.n}"))
                    if(coord_df.at["prevalence_comparison_diagnostic","value"]=="Microscopy"):
                        plot_pfpr_microscopy(site=Site,
                                             plt_dir=os.path.join(f"{self.workdir}/LF_{self.n}"),
                                             wdir=os.path.join(f"{self.workdir}/LF_{self.n}"),
                                             agebin=prevalence_agebin)
                np.savetxt(f"{self.workdir}/emod.ymax.txt", [self.ymax])
                np.savetxt(f"{self.workdir}/LF_{self.n}/emod.ymax.txt", [self.ymax])
            Y0['round'] = [self.n] * len(Y0)
            score_df=pd.read_csv(f"{self.workdir}/all_LL.csv")
            score_df=pd.concat([score_df,Y0])
            score_df.to_csv(f"{self.workdir}/all_LL.csv")
            shutil.copytree(f"{manifest.simulation_output_filepath}",f"{self.workdir}/LF_{self.n}/SO")
            self.n += 1
            np.savetxt(f"{self.workdir}/emod.n.txt", [self.n])
            clean_analyzers()
            #clean_logs()
            clean_COMPS_ID()
        return torch.tensor(xc,dtype=torch.float64), torch.tensor(yc)

problem = Problem(workdir=f"output/{exp_label}")

# at beginning of workflow, cleanup all sbatch scripts for analysis
clean_analyzers()


# Create the GP model
# See emulators/GP.py for a list of GP models
# Or add your own, see: https://botorch.org/docs/models
model = ExactGP(noise_constraint=GreaterThan(1e-6))

# Create batch generator(s)
tts = TurboThompsonSampling(batch_size=emulator_batch_size, 
                            failure_tolerance=failure_limit,
                            success_tolerance=success_limit, 
                            dim=problem.dim) #64

# Create the workflow
bo = BO(problem=problem, model=model, batch_generator=tts, checkpointdir=output_dir, max_evaluations=gp_max_eval)

# Sample and evaluate sets of parameters randomly drawn from the unit cube
#bo.initRandom(2)

bo.initRandom(init_samples,n_batches = init_batches)

# Run the optimization loop
bo.run()

##### Post-calibration steps

# This section calls on the overall post_calibration_analysis pipeline, and
# will only run once the max_eval limit has been reached in the fitting
# process. By default, all relevant steps are included

post_calibration_analysis(experiment=exp_label,
                          length_scales_by_objective=False,           # Fit single-task GP per site-metric (within-host only)
                          length_scales_by_environment_objective=True,# Fit single-task GP per score_type  (environment only)
                          length_scales_plot=True,                    # Plot length-scales for overall score
                          prediction_plot=True,                       # Plot predictions, starting @ exclude_count
                          exclude_count=init_samples,
                          timer_plot=True)                            # Plot emulator and acquisition timing


