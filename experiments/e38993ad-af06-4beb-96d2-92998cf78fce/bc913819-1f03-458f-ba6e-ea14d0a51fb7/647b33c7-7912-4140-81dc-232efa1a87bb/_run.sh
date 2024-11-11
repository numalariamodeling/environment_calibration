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
    
        
                
                    singularity exec --bind /projects/b1139/ipti_pmc/environment_calibration/experiments/e38993ad-af06-4beb-96d2-92998cf78fce/bc913819-1f03-458f-ba6e-ea14d0a51fb7 --bind /projects /projects/b1139/images/dtk_run_rocky_py39.sif Assets/Eradication --config my_config.json --dll-path ./Assets --input-path ./Assets\;.
                
        
    
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