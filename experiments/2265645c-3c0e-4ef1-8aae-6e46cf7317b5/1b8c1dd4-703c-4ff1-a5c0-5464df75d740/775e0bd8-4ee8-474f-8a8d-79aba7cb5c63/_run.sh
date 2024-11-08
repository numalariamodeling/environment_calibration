#!/bin/bash

#SBATCH --signal=B:SIGTERM@30

# define the handler function
term_handler()
{
    # do whatever cleanup you want here
    echo "-1" > job_status.txt
    exit -1
}

# associate the function "term_handler" with the TERM signal
trap 'term_handler' TERM

echo ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} > job_id.txt

n=0
until [ "$n" -ge 1 ]
do
    echo "100" > job_status.txt
    
        
                
                    singularity exec --bind /projects/b1139/ipti_pmc/environment_calibration/experiments/2265645c-3c0e-4ef1-8aae-6e46cf7317b5/1b8c1dd4-703c-4ff1-a5c0-5464df75d740 --bind /projects /projects/b1139/images/dtk_run_rocky_py39.sif Assets/Eradication --config my_config.json --dll-path ./Assets --input-path ./Assets\;.
                
        
    
   RESULT=$?
   if [ $RESULT -eq 0 ]; then
      echo "0" > job_status.txt
      exit $RESULT
   fi
   n=$((n+1))
   sleep 15
done
echo "-1" > job_status.txt
exit $RESULT