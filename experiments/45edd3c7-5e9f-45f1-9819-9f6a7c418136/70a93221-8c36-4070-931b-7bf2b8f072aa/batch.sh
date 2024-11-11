#!/bin/bash

# Set the total number of tasks
total_tasks=10

# Set the number of tasks per array job
batch_size=10

# Set max running jobs
max_jobs=200

num_batches=$((total_tasks / batch_size))
remainder=$((total_tasks % batch_size))

echo "num_batches: $num_batches"
echo "remainder: $remainder"

# Submit the first array job with tasks 1-batch_size
job_id=$(sbatch --array=1-$batch_size%$max_jobs sbatch.sh 0 | awk '{print $4}')
echo $job_id >> job_id.txt

# Submit additional array jobs that depend on the first job
for (( i=1; i<$num_batches; i+=1 ))
do
    # Calculate the task range for the current array job
    start_task=$((i * $batch_size))

    # Submit the array job with the current task range and a dependency on the previous job
    
        new_job_id=$(sbatch --array=1-$batch_size%$max_jobs --dependency=afterok:$job_id sbatch.sh $start_task | awk '{print $4}')
    
    echo $new_job_id >> job_id.txt

    # Update the job ID to use as a dependency for the next array job
    job_id=$new_job_id
done

# Submit the remaining tasks as a separate batch
if [ $remainder -gt 0 ]
then
    start_task=$(($num_batches * $batch_size))

    # Submit the array job with the current task range and a dependency on the previous job
    
        new_job_id=$(sbatch --array=1-$remainder%$max_jobs --dependency=afterok:$job_id sbatch.sh $start_task | awk '{print $4}')
    
    echo $new_job_id >> job_id.txt
fi

wait