# environment_calibration _(PMC adapted version)_


## Background

Our goal is to adapt a botorch multi-objective Bayesian optimization workflow to select EMOD habitat & climate parameters to fit reference site seasonality.

Status Summary

|               | Tested                                                                                               | *Not Yet Tested*                              |
|:-------------:|:------------------------------------|:-------------------|
| Interventions | treatment-seeking<br>non-malaria fever treatment<br>SMC(vaccDrug)<br>bednets (season- and age-dependent) | IRS<br>Campaigns (MSAT/MDA)|
|    Vectors    | *arabiensis*<br>*gambiae*<br>*funestus*                                                              |                                               |
|   Habitats    | constant<br>temporary rainfall<br>water vegetation                                                   | linear spline                                 |

## Instructions

Before following the steps below, please **fork** this repository and clone it to your local machine

For Quest users:

``` bash
#navigate to your home directory or desired project location (ex. /projects/<your_net_id>/)
cd ~

# initialize git
git init

# clone repository and submodules
git clone <ssh path to your fork of the repository> --recursive
```

<details>

<summary>Step 1: Create Virtual Environment</summary>

<br> To start, create a virtual environment containing botorch, idmtools, emodpy, and other required packages.

For Quest users, you can build an environment based off of the existing \<emodpy-torch\> environment.

``` bash
# clone conda-compatible parts of existing virtual environment
conda create --prefix <path/to/env> --name <YOUR_ENVIRONMENT> --clone /projects/b1139/environments/emodpy-torch
```

-   The suggested path/to/env for Quest users is /projects/b1139/environments

    -   Otherwise, the environment will be created in your current working directory, in a new folder called .conda/envs/

-   **Make sure YOUR_ENVIRONMENT is a unique name that doesn't already exist in the folder**

The previous step clones all conda-compatible parts of the virtual environment. It can take a while, but you can expect some terminal output along the way...

``` bash
Source:      /projects/b1139/environments/emodpy-torch 
Destination: /projects/b1139/environments/.conda/envs/<YOUR_ENVIRONMENT> 
Packages: 50 Files: 26196 
Downloading and Extracting Packages 
Preparing transaction: done 
Verifying transaction: done 
Executing transaction: done 
# By downloading and using the cuDNN conda packages, you accept the terms and conditions 
# of the NVIDIA cuDNN EULA - https://docs.nvidia.com/deeplearning/cudnn/sla/index.html # 
# To activate this environment, use 
#     $ conda activate test_torch 
# To deactivate an active environment, use 
#     $ conda deactivate
```

Because some of the packages in the `emodpy-torch` environment were installed using `pip`, they might not make it through the conda clone step. To add them:

``` bash
# Activate your new virtual environment 
source activate <path/to/env>/<YOUR_ENVIRONMENT> # ex. /projects/b1139/environments/my_environment  
# pip install from requirements.txt 
pip install -r /projects/b1139/environments/emodpy-torch/requirements.txt
```

</details>

<details>

<summary>Step 2: Customize site-specific inputs</summary>

<br>

0.  Update **VENV_PATH** in manifest.py and supply the same virtual environment to the placeholder in sbatch_run_calib.sh

1.  Describe reference site simulation options

    -   Example **simulation_coordinator.csv**

        | option                           | value                                       | description                                                          |
        |-----------------|-----------------|--------------------------------------|
        | site                             | Nanoro                                      | site name                                                            |
        | lat                              | 12.68                                       | site latitude                                                        |
        | lon                              | -2.19                                       | site longitude                                                       |
        | climate_start_year               | 2010                                        | First year of climate data to request from ERA5                      |
        | climate_year_dur                 | 10                                          | \# years of climate data to pull from ERA5                           |
        | pop                              | 1000                                        | simulated population                                                 |
        | birth_rate                       | 38                                          | Crude birth rate for site                                            |
        | prev0                            | 0.2                                         | Initial prevalence to supply to demographics file                    |
        | nSims                            | 1                                           | \# of random seeds to simulate                                       |
        | simulation_start_year            | 1960                                        | Day 0 of simulation is Jan 1 of this year                            |
        | simulation_years                 | 60                                          | \# of years to simulate (Jan 1- Dec 31)                              |
        | demographics_filepath            | demographics_files/Nanoro_demographics.json | <site>\_demographics.json if using create_files.py                   |
        | NMF_filepath                     | nonmalarial_fevers/nmf_rates_generic.csv    | blank if not applicable                                              |
        | CM_filepath                      | cm/Nanoro_case_management.csv               | blank if not applicable                                              |
        | SMC_filepath                     |                                             | "file describing SMC campaigns                                       |
        | ITN_filepath                     | itn/Nanoro_ITN.csv                          | "file describing ITN distribution campaigns                          |
        | ITN_age_filepath                 | itn/ITN_age.csv                             | "file describing age-based patterns in ITN usage                     |
        | ITN_season_filepath              | itn/ITN_season.csv                          | "file describing seasonal patterns in ITN usage                      |
        | vector_filepath                  | vectors/vectors.csv                         | file describing mix of vector species and their ecology              |
        | prevalence_comparison            | TRUE                                        | include a measure of prevalence in scoring?                          |
        | prevalence_comparison_reference  | pcr_prevalence_AllAge.csv                   | reference dataset for prevalence                                     |
        | prevalence_comparison_frequency  | monthly                                     | """monthly"" or ""annual"" (not tested)"                             |
        | prevalence_comparison_diagnostic | PCR                                         | """PCR"" or ""Microscopy"" or ""RDT"""                               |
        | incidence_comparison             | TRUE                                        | include a measure of clinical incidence in scoring?                  |
        | incidence_comparison_reference   | routine_incidence_by_district.csv           | reference dataset for incidence                                      |
        | incidence_comparison_frequency   | monthly                                     | """monthly"" or ""annual"""                                          |
        | incidence_comparison_agebin      | 100                                         | agebin (within incidence_comparison_reference) to use for comparison |

    -   Related .csv files for *vectors* and *interventions*

        -   Example: vectors/vectors.csv

            |  species   | fraction | anthropophily | indoor_feeding | constant | temp_rain | water_veg |
            |:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|
            |  gambiae   |   0.9    |     0.74      |      0.9       |    1     |     1     |     0     |
            |  funestus  |   0.05   |      0.5      |      0.86      |    1     |     0     |     1     |
            | arabiensis |   0.05   |     0.88      |      0.5       |    1     |     1     |     0     |

        -   Example: interventions/cm/case_management.csv

            | year | month | day | duration |     trigger     | age_min | age_max |  coverage   | rate | drug |
            |:----:|:-----:|:---:|:--------:|:---------------:|:-------:|:-------:|:-----------:|:----:|:----:|
            | 2005 |   1   |  1  |   1825   | NewClinicalCase |    0    |    5    | 0.153903191 | 0.3  |  AL  |
            | 2005 |   1   |  1  |   1825   | NewClinicalCase |    5    |   15    | 0.092341914 | 0.3  |  AL  |
            | 2005 |   1   |  1  |   1825   | NewClinicalCase |   15    |   115   | 0.061561276 | 0.3  |  AL  |
            | 2005 |   1   |  1  |   1825   |  NewSevereCase  |    0    |   115   |     0.6     | 0.5  |  AL  |
            | 2010 |   1   |  1  |   365    | NewClinicalCase |    0    |    5    | 0.153903191 | 0.3  |  AL  |
            | 2010 |   1   |  1  |   365    | NewClinicalCase |    5    |   15    | 0.092341914 | 0.3  |  AL  |
            | 2010 |   1   |  1  |   365    | NewClinicalCase |   15    |   115   | 0.061561276 | 0.3  |  AL  |
            | 2010 |   1   |  1  |   365    |  NewSevereCase  |    0    |   115   |     0.6     | 0.5  |  AL  |

2.  run **create_files.py** to generate climate and demographics files.

    -   Files created inside simulation_inputs/:
        -   demographics_files/*site*\_demographics.json
        -   site_climate/*site*/...
    -   If you already have files:
        -   supply the path to the desired demographics file inside simulation_coordinator.csv 'demographics_filepath' row
        -   copy climate files into folder site_climate/*site*/

</details>

<details>

<summary>Step 3: Setup calibration algorithm specifications</summary>

<br>

1.  Define input parameter sampling space

    -   Example **parameter_key.csv**

        |               parameter               | min | max | transformation |
        |:-------------------------------------:|:---:|:---:|:--------------:|
        |           Temperature Shift           | -5  |  5  |      none      |
        |      Constant Habitat Multiplier      | -4  |  4  |      log       |
        | Temporary Rainfall Habitat Multiplier | -4  |  4  |      log       |
        |  Water Vegetation Habitat Multiplier  | -4  |  4  |      log       |

2.  Refine scoring system

    -   Example **weights.csv**

        |    objective     | weight |                                     |
        |:----------------:|:------:|-------------------------------------|
        |   shape_score    | 0.001  | *Normalized monthly incidence*      |
        | intensity_score  |  0.1   | *Average annual clinical incidence* |
        | prevalence_score |  0.1   | *Monthly all-age prevalence*        |
        |    eir_score     |  10.0  | *EIR threshold*                     |

3.  Set up calibration scheme

    -   Example **calibration_coordinator.csv**

        | init_size | init_batches | batch_size | max_eval | failure_limit |
        |:---------:|:------------:|:----------:|:--------:|:-------------:|
        |   1000    |      1       |    200     |   5000   |       2       |

</details>

<details>

<summary>Step 4: Run calibration loop</summary>

<br>

1.  edit **run_calib.py** with updated experiment name

2.  run **`sbatch sbatch_run_calib.sh`**

</details>

<details>

<summary>Step 5: Analyze Output</summary>

<br>

The output files automatically created by the calibration loop are found in simulations/output/`exp_label`:

Output from each round of calibration 0-`n_batches`:

-   LF_0/

    -   translated_params.csv

    *Files pertaining to the best-scoring parameter set, if a new one is identified*

    -   emod.best.csv  
        | |parameter|param_set|unit_value|emod_value|min|max|team_default|transformation|type|
        |-|---------|---------|----------|----------|---|---|------------|--------------|----|
        |0|Temperature_Shift|||||||||
        |1|CONST_Multiplier|||||||||
        |2|TEMPR_Multiplier|||||||||
        |3|WATEV_Multiplier|||||||||     
    -   emod.ymax.txt : best score so far, y_max  
    -   EIR_range.csv :  
        | |param_set|minEIR|maxEIR|
        |-|---------|------|------|
        |||||  
    -   ACI.csv  
        | |param_set|agebin|Inc|
        |-|---------|------|------|
        |||||  
    -   incidence\_`site`.png  
        ![alt text](sample_output/incidence_Nanoro.png)
    -   prevalence\_`site`.png
        ![alt text](sample_output/prevalence_Nanoro.png)
      

    *A copy of the simulation_output folder containing analyzed outputs*

    -   SO/`site`/
        -   InsetChart.csv\
        -   ...\
        -   finished.txt

-   ...\

-   LF\_`n_batches`/

    -   translated_params.csv\
    -   SO/`site`/
        -   InsetChart.csv
        -   ...
        -   finished.txt

For any round in which there was an improvement in overall score will contain all of the same files shown above for LF_0. If no improvment, only those shown for LF\_<n_batches> above will appear.

Additionally, plots of score and parameter convergence over time can be produced by running **post_calibration_plots.Rmd**, with the appropriate <exp_label>.

This produces new files inside simulations/output/<exp_label>:

-   performance/
    -   scores/
        -   scores_total.png\
        -   scores_by_objective.png\
    -   parameters/
        -   unit_parameters.png\
        -   emod_parameters.png

</details>

## Methods

### Parameter Space Translation

The GP emulator emplyed by Botorch works with input values $x_{i}$ that are standardized to the unit space $$0,1$$. EMOD parameter values are translated from unit space according to **parameter_key.csv**

If transform=="none" : $x_{emod} = min + x_{i}*(max-min)$

-   Temperature_Shift : Shift (in degrees) to apply to daily air and land temperature series 

If transform=="log" : $x_{emod} = 10^{log10(min)+x_{i}*(log10(max)-log10(min))}$

-   CONSTANT_Multiplier : Scale factor to apply to maximum capacity for mosquito larvae in habitats of type "Constant"
-   TEMPR_Multiplier : Scale factor to apply to maximum capacity for mosquito larvae in habitats of type "Temporary Rainfall"
-   WATEV_Multiplier : Scale factor to apply to maximum capacity for mosquito larvae in habitats of type "Water Vegetation"

### Scoring Simulations vs. Data

Steps taken to report out, analyze, and compare simulation results to targets:

#### Objectives

<details>

<summary>(eir_score) Maximum and minimum monthly EIR</summary>

-   Report: InsetChart
-   Analyzer: InsetChartAnalyzer
-   Output: InsetChart.csv
-   Scoring: `check_EIR_threshold(site)`
    -   Filter to last 10 years of simulation
    -   Sum daily EIR to monthly EIR in each month-year-run
    -   Average EIR in each month-year across runs
    -   Calculate minimum and maximum EIR across all month-years
    -   If any monthly EIR **\>= 100** or any monthly EIR **== 0** : score = 1
        -   Else, score = 0\

</details>

<details>

<summary>(shape_score) Normalized monthly clinical incidence in one age group</summary>

-   Report: MalariaSummaryReport
-   Analyzer: MonthlyIncidenceAnalyzer
-   Output: ClinicalIncidence_monthly.csv
-   Scoring: `compare_incidence_shape(site,agebin)`
    -   Filter to target agebin
    -   Find max incidence each year
    -   Normalize monthly incidence within each year (month / max)
    -   Average normalized incidence per month across years
    -   Score = $log(\frac{pop_{ref}!(pop_{sim}+1)!}{(pop_{ref}+pop_{sim}+1)!} * \frac{(cases_{ref}+(cases_{sim})!}{(cases_{ref}!cases_{sim}!} * \frac{(pop_{ref}-(cases_{ref})!(pop_{sim}-cases_{sim})!}{((pop_{ref}-(cases_{ref})+(pop_{sim}-cases_{sim}))!})$
        -   ${\color{red}\text{Currently hard-coded with presumed reference and simulation population of 1000}}$

</details>

<details>

<summary>(intensity_score) Average annual clinical incidence in one age group</summary>

-   Report: MalariaSummaryReport
-   Analyzer: MonthlyIncidenceAnalyzer
-   Output: ClinicalIncidence_monthly.csv
-   Scoring: `compare_annual_incidence(site,agebin)`
    -   Filter to target agebin
    -   Average annual incidence across months in each year
    -   Average annual incidence across years
    -   Score = $e^{((|incidence_{sim}-incidence_{ref}|) / incidence_{ref})}$

</details>

<details>

<summary>(prevalence_score) All-age PCR prevalence by month and year</summary>

-   Report: InsetChart
-   Analyzer: InsetChart Analyzer
-   Output: InsetChart.csv
-   Scoring: `compare_all_age_PCR_prevalence(site)`
    -   Average PCR Parasite Prevalence in each month-year across runs
    -   Score each month-year as $\sqrt{|prev_{sim}-prev_{ref}|^2}$
    -   Average score across month-years

</details>

<details>

<summary>(pfpr_score) Microscopy prevalence by month and year in one age group ${\color{red}\text{Not yet tested}}$</summary>

-   Report: MalariaSummaryReport\
-   Analyzer: MonthlyPfPRAnalyzer
-   Output: PfPR_monthly.csv
-   Scoring: `compare_PfPR_prevalence(site,agebin)`
    -   Filter to target agebin
    -   Average PfPR in each month-year across runs
    -   Score each month-year as $\sqrt{|pfpr_{sim}-pfpr_{ref}|^2}$
    -   Average score across month-years

</details>

#### Weighting and Summary Score

For each objective_score calculated, a weight is described in **weights.csv**:

Final score = $-\Sigma (objective_score*weight)$  
- If any objective_score is missing or NA, a value of **10** is given post-weighting
- Because the optimization function is a *maximizing* function, we negate the total score

Example: from the simulation with setup

| simulation_coordinator.csv       |         |     |     | weights.csv      |       |
|----------------------------------|---------|-----|-----|------------------|-------|
| incidence_comparison             | TRUE    |     |     | eir_score        | 10    |
| incidence_comparison_frequency   | monthly |     |     | shape_score      | 0.001 |
| incidence_comparison_agebin      | 100     |     |     | intensity_score  | 1     |
| prevalence_comparison            | TRUE    |     |     | prevalence_score | 10    |
| prevalence_comparison_diagnostic | PCR     |     |     |                  |       |

$score= (10\times{}eir\\_score) + (0.001\times{}shape\\_score) + intensity\\_score + (10\times{}prevalence\\_score)$

For the first `init_batches` training rounds:  
- Save the best (highest) score

In later, post-training rounds:

-   If the best score in this round is **worse** (lower) than the current best

    -   `success_counter` resets to zero (or stays there)

    -   `failure_counter` increases by one

-   If the best score in this round is **better** (higher) than the current best

    -   `success_counter` increases by one

    -   `failure_counter` resets to zero (or stays there)

### Emulation

Between rounds, an ExactGP is trained on the $$`batch_size` x `n_parameters`$$ unit input vector $X$ and the [1 x `n_objectives`] score output vector $Y$

The GP is a surrogate model based on a Multivarate Normal Distribution with mean function (my_func) and covariance

-   Mean function is basically my_func : Y(X)

-   Covariance kernel is Matern5/2, which allows the GP propose any function that is 2x differentiable

The model fit to maximize marginal log likelihood has `length_scale` hyperparameters for each input parameter to describe the strength of correlation between scores across values of the parameter

-   This is sort of like the "sensitivity" of the score to changes in the parameter

### TuRBO Thompson Sampling

Initially the Trust Region spans the entire domain $$0,1$$ of each input parameter

-   if `success_counter` meets `success_tolerance` : expand search region proportionally to lengthscales for each parameter, and reset `success_counter` to 0

-   if `failure_counter` meets `failure_tolerance` : shrink search region proportionally to lengthscales for each parameter, and reset `failure_counter` to 0

1.  the GP emulator is used to predict the scores at **5,000** candidate locations in the unit parameter space within the Trust Region

2.  candidate parameter sets with the top `batch_size` predicted scores are selected for the next round of simulation

The process of translating parameters -\> running simulations -\> scoring objectives -\> fitting GP emulator -\> Acquiring samples continues until `max_eval` simulations have been run *and* scored.

## Tips for adding new objectives

To add a new objective (example: vector_species_mix), you may need to

1.  Make changes to files *here* in your project directory to allow for control of new objective

    -   simulation_inputs/simulation_coordinator.csv :
        -   Add logical flag for inclusion (ex. 'vector_mix_comparison')
        -   Add reference_dataset path (ex. 'vector_mix_reference')
    -   simulation_inputs/weights.csv:
        -   Add row with weight for new objective (ex. 'vector_mix_score')

    Different objectives may require more controls (ex. agebin, frequency, diagnostic, etc.)

2.  Make changes to files in your fork of the environment_calibration_common module

    -   helpers.py : add logic for including EMOD reports in simulation
    -   analyzers/analyzer_collection.py : define new analyzer collect simulation output from reporter\
    -   analyzers/analyze.py: add logic for when to require analyzer
    -   compare_to_data/calculate_all_scores.py :
        -   add function to compare outputs of analyzer to reference_data and produce a score by parameter set (ex. 'compare_vector_mix()')
        -   add logic to include scores produced in compute_all_scores()
    -   compare_to_data/run_full_comparison.py :
        -   add logic to compute_scores_across_site() for weighting score and handling missing values
