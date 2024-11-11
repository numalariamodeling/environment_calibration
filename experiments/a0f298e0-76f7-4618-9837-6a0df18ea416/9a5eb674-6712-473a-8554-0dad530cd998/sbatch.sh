#!/bin/bash


#SBATCH --partition=b1139









#SBATCH --time=6:00:00


#SBATCH --account=b1139



#SBATCH --mem=4000


#SBATCH --requeue


#SBATCH --open-mode=append
#SBATCH --output=stdout.txt
#SBATCH --error=stderr.txt




module load singularity



# All submissions happen at the experiment level
srun run_simulation.sh $1
wait

