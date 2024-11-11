#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 12:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8G
#SBATCH --job-name="calibration"
#SBATCH --error=log/calibration.%j.err
#SBATCH --output=log/calibration.%j.out

module purge all

/home/tmh6260/my_environments/pytorch_test/bin/python run_calib.py