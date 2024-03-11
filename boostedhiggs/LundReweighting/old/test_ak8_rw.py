from Utils import *


# f_mc = h5py.File("../TagNTrain/data/BB_UL_MC_small_v2/BB_batch0.h5", "r")
# f_data = h5py.File("../TagNTrain/data/Data_2018C.h5", "r")
f_mc = h5py.File("/uscms_data/d3/oamram/CASE_analysis/src/CASE/CASEUtils/H5_maker/ttbar_output_files/SingleMu_2018C.h5", "r")
f_data = h5py.File(
    "/uscms_data/d3/oamram/CASE_analysis/src/CASE/CASEUtils/H5_maker/ttbar_output_files/TTToSemiLep_2018_small.h5", "r"
)

outdir = "ttbar_rw_test_ak8_old/"

loadMax = 20000
numJets = 2000

pt_min = 200.0
pt_max = 300.0

dr_bin_min = -1.0
dr_bin_max = 8.0
# y_bin_min = np.log(1./0.5)
# y_bin_max = 20*y_bin_min
# y_label = "ln(1/z)"
y_bin_min = -5
y_bin_max = np.log(pt_max)
y_label = "ln(kt)"
n_bins = 20

fill_z = False

ratio_range = [0.5, 1.5]


h_mc = ROOT.TH2F("lp_mc", "Lund Plane MC", n_bins, dr_bin_min, dr_bin_max, n_bins, y_bin_min, y_bin_max)
h_data = ROOT.TH2F("lp_data", "Lund Plane Data", n_bins, dr_bin_min, dr_bin_max, n_bins, y_bin_min, y_bin_max)

# labels_mc = f_mc['truth_label'][:loadMax]
jet_kinematics_mc = f_mc["jet_kinematics"][:loadMax]
all_cands_mc = f_mc["jet1_PFCands"][:loadMax].astype(np.float64)
jet1_feats_mc = f_mc["jet1_extraInfo"][:loadMax]

# no_sig_mask = (labels_mc.reshape(-1) <= 0)
no_sig_mask = jet_kinematics_mc[:, 0] > 0
# pt_cut_mask = (jet_kinematics_mc[:,2] > pt_min) & (jet_kinematics_mc[:,2] < pt_max)
pt_cut_mask = (jet_kinematics_mc[:, 0] > pt_min) & (jet_kinematics_mc[:, 0] < pt_max)

print("sig cut", np.mean(no_sig_mask))
print("pt_cut", np.mean(pt_cut_mask))

cut_cands_mc = all_cands_mc[no_sig_mask & pt_cut_mask]
cut_feats_mc = jet1_feats_mc[no_sig_mask & pt_cut_mask]


jet_kinematics_data = f_data["jet_kinematics"][:loadMax]
all_cands_data = f_data["jet1_PFCands"][:loadMax].astype(np.float64)
jet1_feats_data = f_data["jet1_extraInfo"][:loadMax].astype(np.float64)


# pt_cut_mask_data = (jet_kinematics_data[:,2] > pt_min) & (jet_kinematics_data[:,2] < pt_max)
pt_cut_mask_data = (jet_kinematics_data[:, 0] > pt_min) & (jet_kinematics_data[:, 0] < pt_max)
print("pt_cut data ", np.mean(pt_cut_mask))


cut_cands_data = all_cands_data[pt_cut_mask_data]
cut_feats_data = jet1_feats_data[pt_cut_mask_data]

print(cut_feats_mc.shape, cut_feats_data.shape)

eps = 1e-8


tau21_data = (cut_feats_data[:, 1] / (cut_feats_data[:, 0] + eps))[numJets : 2 * numJets]
tau21_mc = (cut_feats_mc[:, 1] / (cut_feats_mc[:, 0] + eps))[numJets : 2 * numJets]

tau32_data = (cut_feats_data[:, 2] / (cut_feats_data[:, 1] + eps))[numJets : 2 * numJets]
tau32_mc = (cut_feats_mc[:, 2] / (cut_feats_mc[:, 1] + eps))[numJets : 2 * numJets]

tau43_data = (cut_feats_data[:, 3] / (cut_feats_data[:, 2] + eps))[numJets : 2 * numJets]
tau43_mc = (cut_feats_mc[:, 3] / (cut_feats_mc[:, 2] + eps))[numJets : 2 * numJets]

nPF_data = cut_feats_data[:, -1][numJets : 2 * numJets]
nPF_mc = cut_feats_mc[:, -1][numJets : 2 * numJets]

n_bins = 12

make_ratio_histogram(
    [tau21_mc, tau21_data],
    ["MC", "Data"],
    ["b", "r"],
    "Tau21",
    "Tau21 : No Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=None,
    save=True,
    fname=outdir + "tau21_ratio_before.png",
)

make_ratio_histogram(
    [tau32_mc, tau32_data],
    ["MC", "Data"],
    ["b", "r"],
    "tau32",
    "tau32 : No Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=None,
    save=True,
    fname=outdir + "tau32_ratio_before.png",
)

make_ratio_histogram(
    [tau43_mc, tau43_data],
    ["MC", "Data"],
    ["b", "r"],
    "tau43",
    "tau43 : No Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=None,
    save=True,
    fname=outdir + "tau43_ratio_before.png",
)

make_ratio_histogram(
    [nPF_mc, nPF_data],
    ["MC", "Data"],
    ["b", "r"],
    "nPF",
    "nPF : No Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=None,
    save=True,
    fname=outdir + "nPF_ratio_before.png",
)


for i in range(numJets):
    pf_cands_mc = cut_cands_mc[i]
    fill_lund_plane(h_mc, pf_cands_mc, fill_z=fill_z)

    pf_cands_data = cut_cands_data[i]
    fill_lund_plane(h_data, pf_cands_data, fill_z=fill_z)


h_mc.Scale(1.0 / h_mc.Integral())
c_mc = ROOT.TCanvas("c", "", 800, 800)
h_mc.Draw("colz")
h_mc.GetXaxis().SetTitle("ln(0.8/#Delta)")
h_mc.GetYaxis().SetTitle(y_label)
c_mc.Print(outdir + "lundPlane_MC.png")


h_data.Scale(1.0 / h_data.Integral())
c_data = ROOT.TCanvas("c", "", 800, 800)
h_data.Draw("colz")
h_data.GetXaxis().SetTitle("ln(0.8/#Delta)")
h_data.GetYaxis().SetTitle(y_label)
c_data.Print(outdir + "lundPlane_data.png")


h_ratio = h_data.Clone("h_ratio")
h_ratio.SetTitle("Ratio")
h_ratio.Divide(h_mc)
c_ratio = ROOT.TCanvas("c", "", 800, 800)
h_ratio.Draw("colz")
c_ratio.Print(outdir + "lundPlane_ratio.png")

f_out = ROOT.TFile.Open(outdir + "ratio.root", "RECREATE")
h_ratio.Write()
f_out.Close()

LP_weights = []
n_pf_cands = []
for i in range(numJets, 2 * numJets):
    pf_cands_mc = cut_cands_mc[i]
    rw = reweight_lund_plane(h_ratio, pf_cands_mc, fill_z=fill_z)
    LP_weights.append(rw)
    n_pf_cands.append(np.sum(pf_cands_mc[:, 3] > 1e-4))


print(n_pf_cands[:10])
print(nPF_mc[:10])

LP_weights = np.clip(LP_weights, 0.0, 10.0)
print(LP_weights[:10])

weights = [LP_weights, [1.0] * len(tau21_data)]


make_histogram(
    LP_weights,
    "Reweighting factors",
    "b",
    "Weight",
    "Lund Plane Reweighting Factors",
    n_bins,
    normalize=True,
    fname=outdir + "lundPlane_weights.png",
)

make_ratio_histogram(
    [tau21_mc, tau21_data],
    ["MC", "Data"],
    ["b", "r"],
    "Tau21",
    "Tau21 : After Lund Plane Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=weights,
    save=True,
    fname=outdir + "tau21_ratio_after.png",
)

make_ratio_histogram(
    [tau32_mc, tau32_data],
    ["MC", "Data"],
    ["b", "r"],
    "tau32",
    "tau32 : After Lund Plane Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=weights,
    save=True,
    fname=outdir + "tau32_ratio_after.png",
)

make_ratio_histogram(
    [tau43_mc, tau43_data],
    ["MC", "Data"],
    ["b", "r"],
    "tau43",
    "tau43 : After Lund Plane Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=weights,
    save=True,
    fname=outdir + "tau43_ratio_after.png",
)

make_ratio_histogram(
    [nPF_mc, nPF_data],
    ["MC", "Data"],
    ["b", "r"],
    "nPF",
    "nPF : After Lund Plane Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=weights,
    save=True,
    fname=outdir + "nPF_ratio_after.png",
)

make_ratio_histogram(
    [tau21_mc, tau21_mc],
    ["MC RW", "MC"],
    ["b", "r"],
    "Tau21",
    "Tau21 : Lund Plane Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=weights,
    save=True,
    fname=outdir + "tau21_before_vs_after.png",
)

make_ratio_histogram(
    [tau32_mc, tau32_mc],
    ["MC RW", "MC"],
    ["b", "r"],
    "tau32",
    "tau32 : Lund Plane Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=weights,
    save=True,
    fname=outdir + "tau32_before_vs_after.png",
)

make_ratio_histogram(
    [tau43_mc, tau43_mc],
    ["MC RW", "MC"],
    ["b", "r"],
    "tau43",
    "tau43 : Lund Plane Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=weights,
    save=True,
    fname=outdir + "tau43_before_vs_after.png",
)

make_ratio_histogram(
    [nPF_mc, nPF_mc],
    ["MC RW", "MC"],
    ["b", "r"],
    "nPF",
    "nPF : Lund Plane Reweighting",
    n_bins,
    ratio_range=ratio_range,
    normalize=True,
    weights=weights,
    save=True,
    fname=outdir + "nPF_before_vs_after.png",
)
