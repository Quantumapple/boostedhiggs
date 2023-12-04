#!/usr/bin/python

"""
Splits the total fileset and creates condor job submission files for the specified run script.
Author(s): Cristina Mantilla, Raghav Kansal, Farouk Mokhtar
"""
import argparse
import json
import os
from math import ceil

from file_utils import loadFiles


def main(args):
    try:
        proxy = os.environ["X509_USER_PROXY"]
    except ValueError:
        print("No valid proxy. Exiting.")
        exit(1)

    locdir = "condor/" + args.tag + "_" + args.year
    username = os.environ["USER"]
    homedir = f"/store/user/{username}/boostedhiggs/"
    outdir = homedir + args.tag + "_" + args.year + "/"

    # make local directory
    logdir = locdir + "/logs"
    os.system(f"mkdir -p {logdir}")

    # copy the splitting file to the locdir
    os.system(f"cp pfnano_splitting.yaml {locdir}")
    os.system(f"cp {args.config} {locdir}")

    # and condor directory
    print("CONDOR work dir: " + outdir)
    os.system(f"mkdir -p /eos/uscms/{outdir}")

    # build metadata.json with samples
    slist = args.slist.split(",") if args.slist is not None else None
    files, nfiles_per_job = loadFiles(args.config, args.configkey, args.year, args.pfnano, slist)
    metadata_file = f"metadata_{args.configkey}.json"
    with open(f"{locdir}/{metadata_file}", "w") as f:
        json.dump(files, f, sort_keys=True, indent=2)
    print(files.keys())

    # submit a cluster of jobs per sample
    for sample in files.keys():
        print(f"Making directory /eos/uscms/{outdir}/{sample}")
        os.system(f"mkdir -p /eos/uscms/{outdir}/{sample}")

        localcondor = f"{locdir}/{sample}.jdl"
        localsh = f"{locdir}/{sample}.sh"
        try:
            os.remove(localcondor)
            os.remove(localsh)
            os.remove(f"{locdir}/*.log")
        except Exception:
            pass

        tot_files = len(files[sample])
        if args.files_per_job:
            njobs = ceil(tot_files / args.files_per_job)
        else:
            njobs = ceil(tot_files / nfiles_per_job[sample])

        # make submit.txt with number of jobs
        if args.test:
            njobs = 1
        jobids = [str(jobid) for jobid in range(njobs)]
        jobids_file = os.path.join(locdir, f"submit_{sample}.txt")
        with open(jobids_file, "w") as f:
            f.write("\n".join(jobids))

        # make condor file
        condor_templ_file = open("condor/submit.templ.jdl")
        condor_file = open(localcondor, "w")
        for line in condor_templ_file:
            line = line.replace("DIRECTORY", locdir)
            line = line.replace("PREFIX", sample)
            line = line.replace("JOBIDS_FILE", jobids_file)
            line = line.replace("METADATAFILE", metadata_file)
            line = line.replace("PROXY", proxy)
            condor_file.write(line)
        condor_file.close()
        condor_templ_file.close()

        # make executable file
        sh_templ_file = open("condor/submit.templ.sh")
        eosoutput_dir = f"root://cmseos.fnal.gov/{outdir}/{sample}/"
        eosoutput_pkl = f"{eosoutput_dir}/"
        sh_file = open(localsh, "w")
        for line in sh_templ_file:
            line = line.replace("SCRIPTNAME", args.script)
            line = line.replace("YEAR", args.year)
            line = line.replace("METADATAFILE", metadata_file)
            line = line.replace("NUMJOBS", args.n)
            line = line.replace("STARTI", args.starti)
            line = line.replace("SAMPLE", sample)
            line = line.replace("EOSOUTPKL", eosoutput_pkl)

            sh_file.write(line)
        sh_file.close()
        sh_templ_file.close()

        os.system(f"chmod u+x {localsh}")
        if os.path.exists("%s.log" % localcondor):
            os.system("rm %s.log" % localcondor)

        # submit
        if args.submit:
            print("Submit ", localcondor)
            os.system("condor_submit %s" % localcondor)


if __name__ == "__main__":
    """
    python condor/submit.py --year 2017 --tag test
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--script", dest="script", default="run.py", help="script to run", type=str)
    parser.add_argument("--year", dest="year", default="2017", help="year", type=str)
    parser.add_argument("--tag", dest="tag", default="Test", help="process tag", type=str)

    parser.add_argument("--config", dest="config", required=True, help="path to config yaml", type=str)
    parser.add_argument("--key", dest="configkey", required=True, help="config key: [data, mc, ... ]", type=str)
    parser.add_argument("--test", dest="test", action="store_true", help="only 2 jobs per sample will be created")
    parser.add_argument("--submit", dest="submit", action="store_true", help="submit jobs when created")

    parser.add_argument("--starti", dest="starti", default=0, help="start index of files", type=int)
    parser.add_argument("--n", dest="n", default=-1, help="number of files to process", type=int)

    parser.set_defaults(inference=True)
    args = parser.parse_args()

    main(args)
