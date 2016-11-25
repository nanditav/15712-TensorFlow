import argparse
import sys
import subprocess
import os
import time

# CLI parser
parser = argparse.ArgumentParser()
parser.add_argument("--name",help="Specify basename for vms (dont use '_' )")
parser.add_argument("--num_workers", help="Specify number of workers",type=int)
parser.add_argument("--num_parameter_servers", help="Specify number of parameter servers",type=int)
parser.add_argument("--async",help="Specify if the training should be done synchronously or not")
parser.add_argument("--num_sync",help="If async=True, how many workers should be synchronously updated",type=int)
parser.add_argument("--train_steps",help="Specify number of training steps",type=int)
args = parser.parse_args()


# setting up parameters
name = args.name
num_workers = args.num_workers
num_ps = args.num_parameter_servers
async = args.async
num_sync = args.num_sync
train_steps = args.train_steps

#create folder to store output for this experiment
subprocess.call('mkdir ' + name + '_data',shell=True)

progress_ctr = 0
stall_ctr = 0
checkpoint = 0
# code to monitor progress
while(progress_ctr < train_steps):
        time.sleep(30) #check periodically 
        subprocess.call('ssh root@' + name + '-' + str(num_ps) + ' "tail /mnt/train_output.log" > ' + name + '_data/progress.txt',shell=True)
        f = open(name + '_data/progress.txt','r')
        lines = f.readlines()
        temp = lines[len(lines) - 1].strip('\n')
        line = temp.split('\t')
        progress_ctr = int(line[2])
        progress_percent = float(progress_ctr) / float(train_steps)
        print('progress = ' + str(progress_percent*100))
        f.close()
        if progress_ctr - checkpoint > 1000:
                checkpoint = progress_ctr
                subprocess.call('ssh root@' + name + '-0 "vnstat" > ' + name + '_data/temp_nw_stat.txt',shell=True)
                f = open(name + '_data/temp_nw_stat.txt','r')
                lines = f.readlines()
                temp = lines[len(lines) - 3].strip('\n')
                line = temp.split(' ')
                g = open(name + '_data/BW_stats.txt','a')
                g.write('@' + str(checkpoint) + ' ' + line[len(line) - 2] + ' ' + line[len(line) - 1] + '\n')
                g.close()
                f.close()
                subprocess.call('ssh root@' + name + '-0 "vnstat --force --cleartop"',shell=True)

# code to copy stuff to bigdata after completion
# a subdir for checkpoints
subprocess.call('mkdir ' + name + '_data/checkpoints',shell=True)
subprocess.call('scp -r root@' + name + '-' + str(num_ps) + ':/mnt/checkpoint* ' + name + '_data/checkpoints', shell=True)

# for each worker save the train.log and <name>_out.txt
for i in range(len(num_workers)):
        subprocess.call('mkdir ' + name + '_data/workerinfo_' + str(i),shell=True)
        subprocess.call('scp root@' + name + '-' + str(num_ps + i) + ':/mnt/train_output.log ' + name + '_data/workerinfo_' + str(i), shell=True)
        subprocess.call('scp root@' + name + '-' + str(num_ps + i) + ':/mnt/*out.txt ' + name + '_data/workerinfo_' + str(i), shell=True)

