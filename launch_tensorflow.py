#!/usr/bin/python

import os
import sys
import re
import subprocess
import argparse
import time


def command(cmd):
    subprocess.call(cmd,shell=True)
    print(cmd)







parser = argparse.ArgumentParser('Launch tensorflow jobs')

parser.add_argument('-vm-name',required=False,type=str,dest='vm_name',default="tensorflow")
parser.add_argument('-num-workers',required=True,type=int,dest='num_workers')
parser.add_argument('-num-ps',required=True,type=int,dest='num_ps')
args = parser.parse_args()

#Create VMs
command("tashi createMany --basename " + args.vm_name + " --cores 8 --memory 8192 --disks 15712-ubuntu-15.10-server-amd64.qcow2,ext3-900GB.qcow2 --count " +  str(args.num_workers + args.num_ps) )
print("Created VMs.... let's wait for a bit....")

time.sleep(30)
#Create list of ps hosts
ps_hosts = ""
for ps in range(args.num_ps):
    ps_hosts += args.vm_name + "-" + str(args.num_workers + ps) + ":2500"
    if not ps + 1 == args.num_ps:
        ps_hosts += ","


#Create list of worker hosts
worker_hosts = ""
for worker in range(args.num_workers):
    worker_hosts += args.vm_name + "-" + str(worker) + ":2500"
    if not worker + 1 == args.num_workers:
        worker_hosts += ","


for worker in range(args.num_workers):
    work_to_do = "cd tensorflow; git pull base; cd tensorflow/models/image/cifar10; python cifar10_replica.py --ps_hosts=" + ps_hosts + " --worker_hosts=" + worker_hosts + " --job_name=\"worker\" --task_index=" + str(worker) + " --num_gpus=0 --train_steps=10000 --sync_replicas=True &> /mnt/output.log &"
    print("Worker: " + str(worker))
    print("ssh -o StrictHostKeyChecking=no root@" + args.vm_name + "-" + str(worker) + " '" + str(work_to_do) +"'")
    os.system("ssh -o StrictHostKeyChecking=no root@" + args.vm_name + "-" + str(worker) + " '" + str(work_to_do) +"'")

for ps in range(args.num_ps):
    work_to_do = "cd tensorflow; git pull base; cd tensorflow/models/image/cifar10; python cifar10_replica.py --ps_hosts=" + ps_hosts + " --worker_hosts=" + worker_hosts + " --job_name=\"worker\" --task_index=" + str(ps) + " --num_gpus=0 --train_steps=10000 --sync_replicas=True &> /mnt/error.log &"
    print("PS: " + str(ps))
    print("ssh -o StrictHostKeyChecking=no root@" + args.vm_name + "-" + str(ps + args.num_workers) + " '" + str(work_to_do) +"'")
    os.system("ssh -o StrictHostKeyChecking=no root@" + args.vm_name + "-" + str(ps + args.num_workers) + " '" + str(work_to_do) +"'")

#Monitor
while True:
    time.sleep(10) 
    for node in range(args.num_workers + args.num_ps):
        print("Testing node: " + str(node))
        print("Top says: ")
        command("ssh -o StrictHostKeyChecking=no root@" + args.vm_name + "-" +  str(node) + " 'top -b -n2 | grep \"Cpu(s)\"|tail -n 1' > temp.txt")
        f = open("temp.txt");
        usage = f.read()
        print(usage)
        f.close()
        print "\n"
        print("Log says: ")
        command("ssh -o StrictHostKeyChecking=no root@" + args.vm_name + "-" +  str(node) + " 'cat /mnt/output.log | tail -n 5' > temp.txt")
        f = open("temp.txt")
        log = f.read()
        print(log)
        print("---------------------------------------------\n\n")






