#!/bin/bash
### https://github.com/rkansal47/HHbbVV/blob/main/src/HHbbVV/combine/run_blinded.sh

####################################################################################################
# Script for fits
#
# 1) Combines cards and makes a workspace (--workspace / -w)
# 2) Background-only fit (--bfit / -b)
# 3) Expected asymptotic limits (--limits / -l)
# 4) Expected significance (--significance / -s)
# 5) Fit diagnostics (--dfit / -d)
# 6) GoF on data (--gofdata / -g)
# 7) GoF on toys (--unfolding / -t),
# 8) Impacts: initial fit (--impactsi / -i), per-nuisance fits (--impactsf $nuisance), collect (--impactsc $nuisances)
# 9) Bias test: run a bias test on toys (using post-fit nuisances) with expected signal strength
#    given by --bias X.
#
# Specify seed with --seed (default 42) and number of toys with --numtoys (default 100)
#
# Usage ./run_blinded.sh [-wblsdgt] [--numtoys 100] [--seed 42]
####################################################################################################


####################################################################################################
# Read options
####################################################################################################


workspace=0
bfit=0
limits=0
significance=0
dfit=0
dfit_asimov=0
gofdata=0
unfolding=0
impactsi=0
impactsf=0
impactsc=0
seed=444
numtoys=100
bias=-1
mintol=0.5 # --cminDefaultMinimizerTolerance
# maxcalls=1000000000  # --X-rtd MINIMIZER_MaxCalls

options=$(getopt -o "wblsdrgti" --long "workspace,bfit,limits,significance,dfit,dfitasimov,resonant,gofdata,unfolding,impactsi,impactsf:,impactsc:,bias:,seed:,numtoys:,mintol:" -- "$@")
eval set -- "$options"

while true; do
    case "$1" in
        -w|--workspace)
            workspace=1
            ;;
        -b|--bfit)
            bfit=1
            ;;
        -l|--limits)
            limits=1
            ;;
        -s|--significance)
            significance=1
            ;;
        -d|--dfit)
            dfit=1
            ;;
        --dfitasimov)
            dfit_asimov=1
            ;;
        -g|--gofdata)
            gofdata=1
            ;;
        -t|--unfolding)
            unfolding=1
            ;;
        -i|--impactsi)
            impactsi=1
            ;;
        --impactsf)
            shift
            impactsf=$1
            ;;
        --impactsc)
            shift
            impactsc=$1
            ;;
        --seed)
            shift
            seed=$1
            ;;
        --numtoys)
            shift
            numtoys=$1
            ;;
        --mintol)
            shift
            mintol=$1
            ;;
        --bias)
            shift
            bias=$1
            ;;
        --)
            shift
            break;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
    esac
    shift
done

echo "Arguments: workspace=$workspace bfit=$bfit limits=$limits \
significance=$significance dfit=$dfit gofdata=$gofdata unfolding=$unfolding \
seed=$seed numtoys=$numtoys"



####################################################################################################
# Set up fit arguments
#
# We use channel masking to "mask" the blinded and "unblinded" regions in the same workspace.
# (mask = 1 means the channel is turned off)
####################################################################################################

dataset=data_obs
cards_dir="templates/v11/datacards"
# cards_dir="templates/v11/datacards_unfolding"
cp ${cards_dir}/testModel.root testModel.root # TODO: avoid this
CMS_PARAMS_LABEL="CMS_HWW_boosted"

# ####################################################################################################
# # Combine cards, text2workspace, fit, limits, significances, fitdiagnositcs, GoFs
# ####################################################################################################
# # # need to run this for large # of nuisances
# # # https://cms-talk.web.cern.ch/t/segmentation-fault-in-combine/20735


# outdir is the combined directory with the combine.txt datafile
outdir=${cards_dir}/combined
mkdir -p ${outdir}
chmod +x ${outdir}

logsdir=${outdir}/logs
mkdir -p $logsdir
chmod +x ${logsdir}

combined_datacard=${outdir}/combined.txt
ws=${outdir}/workspace.root

# ADD REGIONS
sr1="VBF"
sr2="ggFpt250to350"
sr3="ggFpt350to500"
sr4="ggFpt500toInf"
ccargs="SR1=${cards_dir}/${sr1}.txt SR2=${cards_dir}/${sr2}.txt SR3=${cards_dir}/${sr3}.txt SR4=${cards_dir}/${sr4}.txt"
# ccargs="SR1=${cards_dir}/${sr1}.txt"
# ccargs="SR2=${cards_dir}/${sr2}.txt SR3=${cards_dir}/${sr3}.txt SR4=${cards_dir}/${sr4}.txt"

cr1="TopCR"
cr2="WJetsCR"
ccargs+=" CR1=${cards_dir}/${cr1}.txt CR2=${cards_dir}/${cr2}.txt"


if [ $workspace = 1 ]; then
    echo "Combining cards:"
    for file in $ccargs; do
    echo "  ${file##*/}"
    done
    echo "-------------------------"
    combineCards.py $ccargs > $combined_datacard

    echo "Running text2workspace"

    # single POI
    text2workspace.py $combined_datacard -o $ws 2>&1 | tee $logsdir/text2workspace.txt

    # seperate POIs (to make Table 30 in v11)
    # text2workspace.py $combined_datacard -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose --PO 'map=.*/ggH_hww:r_ggH_hww[1,0,10]' --PO 'map=.*/qqH_hww:r_qqH_hww[1,0,10]' --PO 'map=.*/WH_hww:r_WH_hww[1,0,10]' --PO 'map=.*/ZH_hww:r_ZH_hww[1,0,10]' --PO 'map=.*/ttH_hww:r_ttH_hww[1,0,10]' -o $ws 2>&1

else
    if [ ! -f "$ws" ]; then
        echo "Workspace doesn't exist! Use the -w|--workspace option to make workspace first"
        exit 1
    fi
fi


if [ $significance = 1 ]; then
    echo "Expected significance"

    # single POI
    combine -M Significance -d $ws -m 125 --expectSignal=1 --rMin -1 --rMax 5 -t -1

    # seperate POIs (to make Table 30 in v11 of AN: uncomment either next line for VBF and the one after for ggF)
    # combine -M Significance -d $ws -t -1 --redefineSignalPOIs r_qqH_hww --setParameters r_ggH_hww=1,r_qqH_hww=1,r_WH_hww=1,r_ZH_hww=1,r_ttH_hww=1 --freezeParameters r_WH_hww,r_ZH_hww,r_ttH_hww
    # combine -M Significance -d $ws -t -1 --redefineSignalPOIs r_ggH_hww --setParameters r_ggH_hww=1,r_qqH_hww=1,r_WH_hww=1,r_ZH_hww=1,r_ttH_hww=1 --freezeParameters r_WH_hww,r_ZH_hww,r_ttH_hww

fi

if [ $dfit = 1 ]; then
    echo "Fit Diagnostics"
    combine -M FitDiagnostics -m 125 -d $ws \
    --expectSignal=1 --saveWorkspace --saveToys -n Blinded --ignoreCovWarning \
    --saveShapes --saveNormalizations --saveWithUncertainties --saveOverallShapes 2>&1 | tee $logsdir/FitDiagnosticsBlinded.txt

fi

if [ $dfit_asimov = 1 ]; then

    echo "Fit Diagnostics Asimov"
    combine -M FitDiagnostics -m 125 -d $ws \
    -t -1 --expectSignal=1 --saveWorkspace -n Asimov --ignoreCovWarning \
    --saveShapes --saveNormalizations --saveWithUncertainties --saveOverallShapes 2>&1 | tee $logsdir/FitDiagnosticsAsimov.txt

    # w frequentist toys mean prefit data
    # w/o frequentist toys mean prefit asimov

    # echo "Fit Diagnostics Asimov"
    # combine -M FitDiagnostics -m 125 -d $ws \
    # -t -1 --setParameters r_ggF=1,r_VBF=1,r_VH=1,r_ttH=1 --saveWorkspace --saveToys -n Asimov --ignoreCovWarning \
    # --saveShapes --saveNormalizations --saveWithUncertainties --saveOverallShapes 2>&1 | tee $logsdir/FitDiagnosticsAsimov.txt
    # python diffNuisances.py fitDiagnosticsAsimov.root --abs
fi


if [ $limits = 1 ]; then
    # echo "Expected limits"
    # combine -M AsymptoticLimits -m 125 -n "" -d ${wsm_snapshot}.root --snapshotName MultiDimFit -v 1 \
    # --saveWorkspace --saveToys --bypassFrequentistFit -s $seed \
    # --floatParameters r --toysFrequentist --run blind 2>&1 | tee $logsdir/AsymptoticLimits.txt

    combine -M AsymptoticLimits --run expected -d $ws -t -1  -v 1 --expectSignal 1
fi


if [ $impactsi = 1 ]; then

    echo "Initial fit for impacts"
    # combineTool.py -M Impacts -d $ws -t -1 --rMin -1 --rMax 2 -m 125 --robustFit 1 --doInitialFit   # old

    combineTool.py -M Impacts -d $ws -t -1 --rMin -1 --rMax 2 -m 125 --robustFit 1 --doInitialFit --expectSignal 1
    combineTool.py -M Impacts -d $ws -t -1 --rMin -1 --rMax 2 -m 125 --robustFit 1 --doFits --expectSignal 1 --parallel 50
    combineTool.py -M Impacts -d $ws -t -1 --rMin -1 --rMax 2 -m 125 --robustFit 1 --output impacts.json --expectSignal 1
    plotImpacts.py -i impacts.json -o impacts

fi


# if [ $goftoys = 1 ]; then
#     echo "GoF on toys"
#     combine -M GoodnessOfFit -d $ws --algo=saturated -t 100 -s 1 -m 125 -n Toys
# fi

if [ $gofdata = 1 ]; then
    echo "GoF on data"
    combine -M GoodnessOfFit -d $ws --algo=saturated -s 1 -m 125 -n Observed
fi


# if [ $unfolding = 1 ]; then
#     echo "Combining cards:"
#     for file in $ccargs; do
#     echo "  ${file##*/}"
#     done
#     echo "-------------------------"
#     combineCards.py $ccargs > $combined_datacard

#     # must use datacards_unfolding in cards_dir
#     # must comment the workspace part above

#     text2workspace.py $combined_datacard -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO verbose --PO 'map=.*/ggH_hww_200_300:r_ggH_pt200_300[1,-10,10]' --PO 'map=.*/ggH_hww_300_450:r_ggH_pt300_450[1,-10,10]' --PO 'map=.*/ggH_hww_450_Inf:r_ggH_pt450_inf[1,-10,10]' --PO 'map=.*/qqH_hww:r_qqH_hww[1,-10,10]' --PO 'map=.*/WH_hww:r_WH_hww[1,-10,10]' --PO 'map=.*/ZH_hww:r_ZH_hww[1,-10,10]' --PO 'map=.*/ttH_hww:r_ttH_hww[1,-10,10]' -o $ws 2>&1 | tee $logsdir/text2workspace.txt

#     combine -M MultiDimFit --algo singles -d $ws -t -1 --setParameters r_ggH_pt200_300=1,r_ggH_pt300_450=1,r_ggH_pt450_inf=1,r_qqH_hww=1,r_WH_hww=1,r_ZH_hww=1,r_ttH_hww=1 --freezeParameters r_WH_hww,r_ZH_hww,r_ttH_hww

#     # --- MultiDimFit ---
#     # best fit parameter values and profile-likelihood uncertainties: 
#     # r_ggH_pt200_300 :    +1.000   -1.000/+4.796 (68%)
#     # r_ggH_pt300_450 :    +1.000   -1.000/+1.916 (68%)
#     # r_ggH_pt450_inf :    +1.000   -1.000/+2.523 (68%)
#     #         r_qqH_hww :    +1.000   -0.990/+1.255 (68%)
#     #         r_WH_hww :    +1.000   +0.000/+0.000 (68%)
#     #         r_ZH_hww :    +1.000   +0.000/+0.000 (68%)
#     #         r_ttH_hww :    +1.000   +0.000/+0.000 (68%)
# fi
