"""
Batch I2V Processor for LTX Video
Process multiple images from a JSON job file
"""

import json
import os
import sys
import time
from datetime import datetime
from generate_i2v import load_pipeline, generate_video


def batch_process(job_file, resume_from=0):
    """Process batch jobs from JSON file
    
    Args:
        job_file: Path to JSON file with job definitions
        resume_from: Index to resume from (for interrupted batches)
    
    Returns:
        List of results with status for each job
    """
    # Load jobs
    with open(job_file) as f:
        jobs = json.load(f)
    
    print(f"Loaded {len(jobs)} jobs from {job_file}")
    
    if resume_from > 0:
        print(f"Resuming from job {resume_from}")
        jobs = jobs[resume_from:]
    
    # Load pipeline once
    pipe = load_pipeline()
    
    results = []
    start_time = time.time()
    
    for i, job in enumerate(jobs):
        job_num = i + resume_from + 1
        total_jobs = len(jobs) + resume_from
        
        print(f"\n{'='*50}")
        print(f"Processing {job_num}/{total_jobs}: {job['name']}")
        print(f"{'='*50}")
        
        try:
            path = generate_video(
                pipe,
                job['image'],
                job['prompt'],
                job['name'],
                job.get('seed', 42)
            )
            results.append({
                'name': job['name'],
                'status': 'success',
                'path': path
            })
        except Exception as e:
            print(f"ERROR: {str(e)}")
            results.append({
                'name': job['name'],
                'status': 'error',
                'error': str(e)
            })
        
        # Progress update
        elapsed = time.time() - start_time
        completed = i + 1
        avg_time = elapsed / completed
        remaining = (len(jobs) - completed) * avg_time
        
        print(f"\nProgress: {completed}/{len(jobs)} | "
              f"Avg: {avg_time:.1f}s/video | "
              f"ETA: {remaining/60:.1f} min")
    
    # Summary
    total_time = time.time() - start_time
    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'error')
    
    print(f"\n{'='*50}")
    print(f"BATCH COMPLETE")
    print(f"{'='*50}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Success: {success}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print(f"Avg time per video: {total_time/len(results):.1f}s")
    
    return results


def create_sample_jobs():
    """Create a sample jobs.json file"""
    sample = [
        {
            "name": "intro_video_1",
            "image": "/workspace/inputs/thumbnail1.jpg",
            "prompt": "Slow zoom in on the subject, subtle breathing motion, professional lighting",
            "seed": 123
        },
        {
            "name": "cityscape_broll",
            "image": "/workspace/inputs/city.jpg",
            "prompt": "Time-lapse motion, clouds moving slowly across the sky, static camera",
            "seed": 456
        },
        {
            "name": "presenter_talking",
            "image": "/workspace/inputs/presenter.jpg",
            "prompt": "Subtle head movement, natural eye blinks, slight gestures while speaking",
            "seed": 789
        }
    ]
    
    with open("sample_jobs.json", "w") as f:
        json.dump(sample, f, indent=2)
    
    print("Created sample_jobs.json")
    print("Edit this file with your actual image paths and prompts")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_process.py <jobs.json> [resume_from_index]")
        print("       python batch_process.py --create-sample")
        sys.exit(1)
    
    if sys.argv[1] == "--create-sample":
        create_sample_jobs()
    else:
        job_file = sys.argv[1]
        resume_from = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        
        results = batch_process(job_file, resume_from)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"batch_results_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
