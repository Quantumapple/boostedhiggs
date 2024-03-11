import sys, os

sys.path.insert(0, "")
sys.path.append("../")
from Utils import *


parser = input_options()
options = parser.parse_args()
tdrstyle.setTDRStyle()

print(options)

# UL
if options.year == 2018:
    lumi = 59.74
    year = 2018
    f_dir = "/uscms_data/d3/oamram/CASE_analysis/src/CASE/LundReweighting/Lund_output_files_2018/"

elif options.year == 2017:
    lumi = 41.42
    year = 2017
    f_dir = "/uscms_data/d3/oamram/CASE_analysis/src/CASE/LundReweighting/Lund_output_files_2017/"

elif options.year == 2016:
    year = 2016
    lumi = 16.8 + 19.5
    f_dir = "/uscms_data/d3/oamram/CASE_analysis/src/CASE/LundReweighting/Lund_output_files_2016/"
else:
    exit(1)

f_data = h5py.File(f_dir + "SingleMu_merge.h5", "r")
f_ttbar = h5py.File(f_dir + "TT.h5", "r")
f_wjets = h5py.File(f_dir + "QCD_WJets.h5", "r")
f_diboson = h5py.File(f_dir + "diboson.h5", "r")
f_tw = h5py.File(f_dir + "TW.h5", "r")
f_singletop = h5py.File(f_dir + "SingleTop_merge.h5", "r")


# f_ratio = ROOT.TFile.Open("ttbar_UL_jan20_W_rw_kt_sys/ratio.root")
f_ratio = ROOT.TFile.Open(options.fin)


# for SF computation
tau32_cut = 0.52


outdir = options.outdir
if not os.path.exists(outdir):
    os.system("mkdir %s" % outdir)
do_sys_variations = not options.no_sys

max_evts = None

norm = True

jms_corr = 1.0

m_cut_min = 125.0
# m_cut_max = 130.
m_cut_max = 225.0
pt_cut = 500.0

if not os.path.exists(outdir):
    os.system("mkdir " + outdir)

d_data = Dataset(f_data, is_data=True)

d_tw = Dataset(f_tw, label="tW", color=ROOT.kYellow - 7, jms_corr=jms_corr)
d_wjets = Dataset(f_wjets, label="W+Jets + QCD", color=ROOT.kOrange - 3, jms_corr=jms_corr)
d_diboson = Dataset(f_diboson, label="Diboson", color=ROOT.kCyan, jms_corr=jms_corr)
d_singletop = Dataset(f_singletop, label="Single Top", color=ROOT.kMagenta - 1, jms_corr=jms_corr)


d_ttbar_w_match = Dataset(f_ttbar, label="t#bar{t} : W-matched", color=ROOT.kRed - 7, jms_corr=jms_corr, dtype=2)
d_ttbar_t_match = Dataset(f_ttbar, label="t#bar{t} : t-matched", color=ROOT.kBlue - 7, jms_corr=jms_corr, dtype=3)
d_ttbar_nomatch = Dataset(f_ttbar, label="t#bar{t} : unmatched", color=ROOT.kGreen - 6, jms_corr=jms_corr)

ttbar_gen_matching = d_ttbar_w_match.f["gen_parts"][:, 0]

# 0 is unmatched, 1 is W matched, 2 is top matched
nomatch_cut = ttbar_gen_matching < 0.1
w_match_cut = (ttbar_gen_matching > 0.9) & (ttbar_gen_matching < 1.1)
t_match_cut = (ttbar_gen_matching > 1.9) & (ttbar_gen_matching < 2.1)

d_ttbar_w_match.apply_cut(w_match_cut)
d_ttbar_t_match.apply_cut(t_match_cut)
d_ttbar_nomatch.apply_cut(nomatch_cut)


sigs = [d_ttbar_t_match]
# removed d_diboson
bkgs = [d_singletop, d_wjets, d_tw, d_ttbar_w_match, d_ttbar_nomatch]


pt_max = 1000


dr_bin_min = -1.0
dr_bin_max = 8.0
# y_bin_min = np.log(1./0.5)
# y_bin_max = 20*y_bin_min
# y_label = "ln(1/z)"
kt_bin_min = -5
kt_bin_max = np.log(pt_max)
z_label = "ln(kt/GeV)"
y_label = "ln(0.8/#Delta)"
n_bins_LP = 20
n_bins = 20

kt_bins = array("f", np.linspace(kt_bin_min, kt_bin_max, num=n_bins_LP + 1))

dr_bins = array("f", np.linspace(dr_bin_min, dr_bin_max, num=n_bins_LP + 1))


fill_z = False

jetR = 1.0

# jetR = 0.4

num_excjets = 3


ratio_range = [0.2, 1.8]


jet_kinematics_data = f_data["jet_kinematics"][()]
msd_cut_data = (jet_kinematics_data[:, 3] > m_cut_min) & (jet_kinematics_data[:, 3] < m_cut_max)
pt_cut_data = jet_kinematics_data[:, 0] > pt_cut
d_data.apply_cut(msd_cut_data & pt_cut_data)
d_data.compute_obs()

for d in bkgs + sigs:

    d.norm_factor = lumi

    jet_kinematics = d.f["jet_kinematics"][:]
    msd_cut_mask = (jet_kinematics[:, 3] * jms_corr > m_cut_min) & (jet_kinematics[:, 3] * jms_corr < m_cut_max)
    pt_cut_mask = jet_kinematics[:, 0] > pt_cut
    d.apply_cut(msd_cut_mask & pt_cut_mask)
    d.compute_obs()


# print("Num data %i. Num ttbar MC %i " % (d_data.n(), d_ttbar.n()))


num_data = np.sum(d_data.get_weights())
num_ttbar_nomatch = np.sum(d_ttbar_nomatch.get_weights())
num_ttbar_w_match = np.sum(d_ttbar_w_match.get_weights())
num_ttbar_t_match = np.sum(d_ttbar_t_match.get_weights())
num_ttbar_tot = num_ttbar_nomatch + num_ttbar_w_match + num_ttbar_t_match
num_tw = np.sum(d_tw.get_weights())

tot_bkg = 0.0
for d in (d_diboson, d_wjets, d_singletop):
    tot_bkg += np.sum(d.get_weights())
print(
    "%i data, %.0f ttbar (%.0f unmatched, %.0f W matched, %.0f t matched), %.0f tW %.0f bkg"
    % (num_data, num_ttbar_tot, num_ttbar_nomatch, num_ttbar_w_match, num_ttbar_t_match, num_tw, tot_bkg)
)
normalization = num_data / (num_ttbar_tot + num_tw + tot_bkg)
print("normalization", normalization)

if norm:
    for d in bkgs + sigs:
        d.norm_factor *= normalization


obs = ["tau21", "tau32", "tau43", "nPF", "mSoftDrop", "pt"]


obs_attrs = {
    "mSoftDrop": (125, 225, 25, "m_{SD} [GeV]", "Events / 4 GeV"),
    "tau21": (0.05, 0.8, 15, "#tau_{21}", "Events / 0.05"),
    "tau32": (0.2, 0.95, 15, "#tau_{32}", "Events / 0.05"),
    "tau43": (0.6, 0.96, 18, "#tau_{43}", "Events / 0.02"),
    "nPF": (20.5, 120.5, 25, "Num. PF Cands.", "Events / 4"),
    "pt": (500, 1200.0, 20, "p_{T}", ""),
}

colors = []
weights_nom = []
labels = []
for d in bkgs + sigs:
    colors.append(d.color)
    weights_nom.append(d.get_weights())
    labels.append(d.label)

for l in obs:
    a = []
    for d in bkgs + sigs:
        a.append(getattr(d, l))
    a_data = getattr(d_data, l)

    (
        low,
        high,
        nbins_,
        label,
        ylabel,
    ) = obs_attrs.get(l, (None, None, 20, l, ""))

    make_multi_sum_ratio_histogram(
        data=a_data,
        entries=a,
        weights=weights_nom,
        labels=labels,
        uncs=None,
        h_range=(low, high),
        drawSys=False,
        stack=True,
        draw_chi2=True,
        year=year,
        colors=colors,
        axis_label=label,
        title=l + " : LP Reweighting",
        num_bins=nbins_,
        normalize=False,
        ratio_range=ratio_range,
        fname=outdir + l + "_ratio_before.png",
    )


weights_rw = copy.deepcopy(weights_nom)

h_ratio = f_ratio.Get("ratio_nom")

if "pt_extrap" in f_ratio.GetListOfKeys() and not options.no_pt_extrap:
    rdir = f_ratio.GetDirectory("pt_extrap")
    rdir.cd()

else:
    print("NO Pt extrapolation")
    rdir = None

nToys = 100

# Noise used to generated smeared ratio's based on stat unc
rand_noise = np.random.normal(size=(nToys, h_ratio.GetNbinsX(), h_ratio.GetNbinsY(), h_ratio.GetNbinsZ()))
pt_rand_noise = np.random.normal(size=(nToys, h_ratio.GetNbinsY(), h_ratio.GetNbinsZ(), 3))

LP_rw = LundReweighter(jetR=jetR, pt_extrap_dir=rdir, charge_only=options.charge_only)


d_sig = sigs[0]

sig_idx = len(bkgs)
print("Reweighting ", d.f)
subjets, splittings, bad_match, deltaRs = d_sig.get_matched_splittings(
    LP_rw, num_excjets=num_excjets, return_dRs=True, rescale_subjets="jec"
)
d_LP_weights, d_LP_smeared_weights, d_pt_smeared_weights = d_sig.reweight_LP(
    LP_rw,
    h_ratio,
    num_excjets=num_excjets,
    prefix="",
    rand_noise=rand_noise,
    pt_rand_noise=pt_rand_noise,
    subjets=subjets,
    splittings=splittings,
)


subjet_responses = []
jet_responses = []

gen_parts_raw = d_sig.get_masked("gen_parts")[:]
top = gen_parts_raw[:, 1:5]
antitop = gen_parts_raw[:, 5:9]
W = gen_parts_raw[:, 9:13]
antiW = gen_parts_raw[:, 13:17]
q1 = gen_parts_raw[:, 17:20]
q2 = gen_parts_raw[:, 21:24]
b = gen_parts_raw[:, 25:28]
gen_parts = np.stack([q1, q2, b], axis=1)


j_4vec = d_sig.get_masked("jet_kinematics")[:, :4].astype(np.float64)


for i, sjs in enumerate(subjets):

    if bad_match[i]:
        continue
    if deltaR(top[i], j_4vec[i]) < deltaR(antitop[i], j_4vec[i]):
        jet_responses.append(j_4vec[i][0] / top[i][0])

    else:
        jet_responses.append(j_4vec[i][0] / antitop[i][0])

    subjet_responses.append(d_sig.get_pt_response(gen_parts[i], subjets[i]))

make_histogram(
    np.array(subjet_responses).reshape(-1),
    "Top subjets",
    "b",
    "Subjet pt / gen pt",
    "Subjet pt response ",
    20,
    h_range=(0.5, 1.5),
    normalize=True,
    fname=outdir + "subjet_response.png",
    mean_std=True,
)

make_histogram(
    np.array(jet_responses).reshape(-1),
    "Top jets",
    "b",
    "Top jet pt / gen pt",
    "Top jet pt response ",
    20,
    h_range=(0.5, 1.5),
    normalize=True,
    fname=outdir + "jet_response.png",
    mean_std=True,
)


f_ratio.cd("pt_extrap")

LP_weights = d_LP_weights

# apply weights, keep normalization fixed
old_norm = np.sum(weights_rw[sig_idx])
weights_rw[sig_idx] *= d_LP_weights

new_norm = np.sum(weights_rw[sig_idx])


weights_rw[sig_idx] *= old_norm / new_norm
LP_smeared_weights = np.array(d_LP_smeared_weights * np.expand_dims(weights_nom[sig_idx], -1) * (old_norm / new_norm))
pt_smeared_weights = np.array(d_pt_smeared_weights * np.expand_dims(weights_nom[sig_idx], -1) * (old_norm / new_norm))


sys_variations = dict()
if do_sys_variations:
    # sys_list = list(sys_weights_map.keys())
    sys_list = ["sys_tot_up", "sys_tot_down"]
    for sys in sys_list:
        if sys == "nom_weight":
            continue
        sys_ratio = f_ratio.Get("ratio_" + sys)
        sys_ratio.Print()
        sys_str = sys + "_"

        sys_LP_weights = d_sig.reweight_LP(
            LP_rw, sys_ratio, num_excjets=num_excjets, prefix="", sys_str=sys_str, subjets=subjets, splittings=splittings
        )

        sys_weights = weights_nom[sig_idx] * sys_LP_weights
        rw = np.sum(weights_nom[sig_idx]) / np.sum(sys_weights)
        sys_weights *= rw
        sys_variations[sys] = sys_weights

    if f_ratio.GetListOfKeys().Contains("h_bl_ratio"):
        b_light_ratio = f_ratio.Get("h_bl_ratio")
        bquark_rw = d.reweight_LP(
            LP_rw,
            b_light_ratio,
            num_excjets=num_excjets,
            prefix="",
            max_evts=max_evts,
            sys_str="bquark",
            subjets=subjets,
            splittings=splittings,
        )
    else:
        print("bl ratio not found. skipping b quark uncs.")
        bquark_rw = np.ones_like(weights_rw[sig_idx])

    up_bquark_weights = bquark_rw * weights_rw[sig_idx]
    down_bquark_weights = (1.0 / bquark_rw) * weights_rw[sig_idx]

    up_bquark_weights *= old_norm / np.sum(up_bquark_weights)
    down_bquark_weights *= old_norm / np.sum(down_bquark_weights)

    sys_variations["bquark_up"] = up_bquark_weights
    sys_variations["bquark_down"] = down_bquark_weights


clip_weights = np.clip(LP_weights, 0.0, 5.0)
make_histogram(
    clip_weights,
    "Reweighting factors",
    "b",
    "Weight",
    "Lund Plane Reweighting Factors",
    20,
    h_range=(0.0, 5.0),
    normalize=False,
    fname=outdir + "lundPlane_weights.png",
)


# Save subjet pts and deltaR
subjet_pts = []
deltaRs = np.reshape(deltaRs, -1)

for i, sjs in enumerate(subjets):
    for sj in sjs:
        subjet_pts.append(sj[0])

num_bins = 40
pt_bins = array("d", np.linspace(0.0, 800.0, num_bins + 1))
response_bins = array("d", np.linspace(0.5, 1.5, num_bins + 1))
dR_bins = array("d", np.linspace(0.0, 0.8, num_bins + 1))

h_subjet_pts = make_root_hist(data=subjet_pts, name="h_top_subjetpt", num_bins=num_bins, bins=pt_bins)
# h_subjet_response = make_root_hist(data = subjet_responses, name = 'subjet_responses', num_bins = num_bins, bins = response_bins)
h_dRs = make_root_hist(data=deltaRs, name="h_top_dRs", num_bins=num_bins, bins=dR_bins)
f_ptout = ROOT.TFile.Open(outdir + "subjet_pt_dR.root", "RECREATE")
h_subjet_pts.Write()
h_dRs.Write()
f_ptout.Close()


print("Fraction of subjets with pt > 350 : %.3f" % (np.mean(np.array(subjet_pts).reshape(-1) > 350.0)))


# compute 'Scalefactor'
cut = d_ttbar_t_match.tau32 < tau32_cut

eff_nom = np.average(cut, weights=weights_nom[sig_idx])
eff_rw = np.average(cut, weights=weights_rw[sig_idx])

print("Nom %.3f, RW %.3f" % (eff_nom, eff_rw))


eff_toys = []
pt_eff_toys = []
for i in range(nToys):
    eff = np.average(cut, weights=LP_smeared_weights[:, i])
    eff_toys.append(eff)

    eff1 = np.average(cut, weights=pt_smeared_weights[:, i])
    pt_eff_toys.append(eff1)

toys_mean = np.mean(eff_toys)
toys_std = np.std(eff_toys)

print("Toys avg %.3f, std dev %.3f" % (toys_mean, toys_std))

pt_toys_mean = np.mean(pt_eff_toys)
pt_toys_std = np.std(pt_eff_toys)

print("Pt variation toys avg %.3f, std dev %.3f" % (pt_toys_mean, pt_toys_std))

# Add systematic differences in quadrature
SF_sys_unc = SF_bquark_unc = 0.0
if do_sys_variations:

    eff_sys_tot_up = np.average(cut, weights=sys_variations["sys_tot_up"])
    eff_sys_tot_down = np.average(cut, weights=sys_variations["sys_tot_down"])
    SF_sys_unc_up = abs(eff_sys_tot_up - eff_rw) / eff_nom
    SF_sys_unc_down = abs(eff_sys_tot_down - eff_rw) / eff_nom
    SF_sys_unc = (SF_sys_unc_up + SF_sys_unc_down) / 2.0

    eff_bquark_up = np.average(cut, weights=sys_variations["bquark_up"])
    eff_bquark_down = np.average(cut, weights=sys_variations["bquark_down"])
    SF_bquark_up = abs(eff_bquark_up - eff_rw) / eff_nom
    SF_bquark_down = abs(eff_bquark_down - eff_rw) / eff_nom
    SF_bquark_unc = (SF_bquark_up + SF_bquark_down) / 2.0


SF = eff_rw / eff_nom
SF_stat_unc = abs(toys_mean - eff_rw) / eff_nom + toys_std / eff_nom
SF_pt_unc = abs(pt_toys_mean - eff_rw) / eff_nom + pt_toys_std / eff_nom

bad_matching_unc = np.mean(bad_match) * SF

print(
    "\n\nSF (cut val %.2f ) is %.2f +/- %.2f  (stat) +/- %.2f (sys) +/- %.2f (pt) +/- %.2f (bquark) +/- %.2f (matching) \n\n"
    % (tau32_cut, SF, SF_stat_unc, SF_sys_unc, SF_pt_unc, SF_bquark_unc, bad_matching_unc)
)

f_ratio.Close()

# approximate uncertainty on the reweighting for the plots
overall_unc = (SF_stat_unc**2 + SF_sys_unc**2 + SF_pt_unc**2 + SF_bquark_unc**2 + bad_matching_unc**2) ** 0.5 / SF
print("overall unc %.3f" % overall_unc)

uncs_rw = [np.zeros_like(rw) for rw in weights_rw]
uncs_rw[len(bkgs)] = overall_unc * weights_rw[len(bkgs)]


for l in obs:
    a = []
    for d in bkgs + sigs:
        a.append(getattr(d, l))
    a_data = getattr(d_data, l)

    low, high, nbins_, label, ylabel = obs_attrs.get(l, (None, None, 20, l, ""))

    make_multi_sum_ratio_histogram(
        data=a_data,
        entries=a,
        weights=weights_rw,
        labels=labels,
        uncs=uncs_rw,
        h_range=(low, high),
        drawSys=False,
        stack=True,
        draw_chi2=True,
        year=year,
        colors=colors,
        axis_label=label,
        title=l + " : LP Reweighting",
        num_bins=nbins_,
        normalize=False,
        ratio_range=ratio_range,
        fname=outdir + l + "_ratio_after.png",
    )
