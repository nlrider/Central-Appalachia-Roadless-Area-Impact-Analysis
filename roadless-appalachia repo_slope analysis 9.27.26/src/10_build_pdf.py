"""Builds the technical comment PDF from figures and computed outputs (numbers pulled from data/processed where tabulated)."""
import json
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle,
                                PageBreak, KeepTogether)

INK, INK2, BLUE = colors.HexColor("#1a1a1a"), colors.HexColor("#555555"), colors.HexColor("#184f95")
OUT = "outputs/Technical_Comment_Roadless_Appalachia.pdf"

body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.6, leading=13.2, textColor=INK, spaceAfter=6, alignment=TA_LEFT)
small = ParagraphStyle("small", parent=body, fontSize=8, leading=10.5, textColor=INK2, spaceAfter=3)
h1 = ParagraphStyle("h1", parent=body, fontName="Helvetica-Bold", fontSize=12.5, leading=15, textColor=BLUE, spaceBefore=10, spaceAfter=5, keepWithNext=1)
h2 = ParagraphStyle("h2", parent=body, fontName="Helvetica-Bold", fontSize=10.3, leading=13, spaceBefore=6, spaceAfter=3, keepWithNext=1)
title = ParagraphStyle("title", parent=body, fontName="Helvetica-Bold", fontSize=19, leading=23, spaceAfter=4)
sub = ParagraphStyle("sub", parent=body, fontSize=10.5, leading=14, textColor=INK2, spaceAfter=8)
bul = ParagraphStyle("bul", parent=body, leftIndent=14, bulletIndent=3, spaceAfter=3.5)
cap = ParagraphStyle("cap", parent=small, spaceAfter=8)
cell = ParagraphStyle("cell", parent=body, fontSize=8.2, leading=10, spaceAfter=0)


def P(t, s=body): return Paragraph(t, s)
def B(t): return Paragraph(t, bul, bulletText="•")
def fig(path, w=7.0):
    from PIL import Image as PI
    iw, ih = PI.open(path).size
    return Image(path, width=w * inch, height=w * inch * ih / iw)


def footer(c, d):
    c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(INK2)
    c.drawString(0.75 * inch, 0.45 * inch, "Technical comment on FS-2025-0001 | Appalachian national forests | Code and data: see Section 8")
    c.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Page {d.page}")
    c.restoreState()


doc = BaseDocTemplate(OUT, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.7 * inch, bottomMargin=0.8 * inch,
                      title="Technical Comment: Terrain, Hazard and Water Context of Inventoried Roadless Areas in Core Appalachian National Forests",
                      author="[Author name]")
doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=footer)])

scr = pd.read_csv("data/processed/agency_screen_by_forest.csv")
water = json.load(open("data/processed/water_summary.json"))
S = []

# ---------- title block ----------
S += [P("Technical Comment on the Proposed Rescission of the 2001 Roadless Area Conservation Rule", title),
      P("Terrain, operability, landslide and drinking-water context for inventoried roadless areas in the core Appalachian national forests", sub),
      P("<b>Docket:</b> FS-2025-0001 (USDA Forest Service; Draft Environmental Impact Statement (DEIS) and Economic Analysis)<br/>"
        "<b>Submitted by:</b> [Name, credentials, affiliation for identification only]<br/>"
        "<b>Date:</b> [Date of submission]", body),
      P("<i>This comment is submitted in my personal capacity. It does not represent the views of my employer or any institution. "
        "[Confirm any institutional policy on outside comments before submitting.] It is an analytic comment on the evidence; "
        "the author has separately filed a comment stating a position. Submission deadline: verify on Regulations.gov (the Federal Register notice and later extension notices differ).</i>", small)]

# ---------- 1 summary ----------
S += [P("1. Summary", h1),
      P("I analyzed 411 inventoried roadless area (IRA) polygons, 922,990 acres, in seven forest groupings of the core southern and central Appalachians "
        "(George Washington and Jefferson, Monongahela, Pisgah-Nantahala, Cherokee, Chattahoochee, Allegheny, Daniel Boone). This is about 1.6% of IRA acreage nationally, "
        "so the results describe Appalachian conditions and should not be extrapolated. Using public data and the Draft EIS's own operability criteria, I find:"),
      B("<b>Steep terrain does not, by itself, protect most of this land.</b> About 61% of roadless acres exceed 35% slope and 42% exceed 45% (10 m DEM), yet applying the Draft EIS screen "
        "(slope and distance to existing roads) classifies 31% as likely operable, 55% as operable but complex, and only 14% as likely not operable."),
      B("<b>Roadless land is generally steeper and more remote than land the Forest Service has recently harvested,</b> but the distributions overlap. "
        "In the same forests, 89% of harvest acreage since FY2001 falls in the likely operable class (partly by construction, since harvest requires roads). "
        "Between 41% and 84% of roadless acres in each forest are no steeper than that forest's own 90th-percentile harvest slope."),
      B("<b>The screen is sensitive to inputs the Draft EIS does not disclose.</b> Moving the slope thresholds by 10 points changes the likely operable share from 20% to 42%. "
        "Coarser terrain data classify more land as operable: 43% of roadless acres exceed 40% slope on a 30 m DEM versus 52% on a 10 m DEM."),
      B("<b>Roadless areas coincide with failure-prone ground.</b> Mapped Hurricane Helene landslides were about five times as dense in roadless areas (0.48 per 1,000 acres) as on other national forest land "
        "in the same area (0.10). This is descriptive; it is not evidence that any road or harvest caused a landslide."),
      B("<b>Hundreds of thousands of people drink water from watersheds that contain roadless land.</b> Depending on definition, 258,000 to 534,000 people are served by "
        "98 to 139 surface-water intakes located in such watersheds (primary definition: about 454,000)."),
      P("I ask the agency to disaggregate its analysis for the Eastern and Southern regions, disclose the operability method and inputs, quantify landslide and water-quality risk for these forests, and "
        "analyze exposure to future forest-plan amendments (Section 6).")]

# ---------- 2 what the DEIS says ----------
S += [P("2. What the Draft EIS says about this region", h1),
      P("The Draft EIS reports that under Alternative 2 (full rescission) about 4.8 million acres, 16% of forested potentially affected IRA acres, are operable or complex <i>and</i> allowed or generally allowed timber harvest under current plans; "
        "the Southern Region figure is about 148,000 acres of 839,340 IRA acres. It states that the Eastern and Southern regions have the largest share of likely operable land, "
        "and that about 40% of potentially affected IRA in the Southern Region is likely operable. Plans generally allow harvest on 13.4 million acres (33.4%) and road construction on 18.2 million acres (45.5%) of the roughly 40 million potentially affected acres, "
        "and plan amendments could expand those areas over time. The Economic Analysis estimates Forest Service revenue of $5.2 to $11.4 million per year nationally (a 5 to 10% increase in sawtimber harvest) and producer surplus to industry of $4.6 to $10.6 million per year.")]
S += [P("The agency figures are regional aggregates and are not directly comparable to the forest-level estimates below, because they apply forest-plan restrictions and productivity that I do not model, "
        "and because the Eastern and Southern regions include national forests outside my study area. That is the reason for the disaggregation request in Section 6.")]

# ---------- 3 methods ----------
S += [P("3. Data and methods", h1),
      P("<b>Study area.</b> 2001 IRA polygons (USFS EDW) in the core forests above. Slope was computed from the USGS 3DEP 1/3 arc-second (about 10 m) DEM using Horn's method, by polygon and tile (pixels are assigned to one tile only, so overlaps are not double-counted). "
        "DEM-derived area (918,434 acres) is within 0.5% of official IRA acreage. A second, independent script reproduces the slope histograms exactly."),
      P("<b>Operability screen.</b> I implemented the Draft EIS criteria (Vol. I, pp. 73-74) on 10 m cells: likely operable = within 0.5 mile of a road, under 40% slope; operable but complex = "
        "(within 0.5 mile and 40 to 70% slope) or (0.5 to 1 mile and under 70% slope); otherwise likely not operable. Site productivity and statutory or plan restrictions are not applied, so "
        "the operable share is an upper bound on what the full screen would give. Distance to roads uses USGS TNM/TIGER roads and USFS system roads (227,525 segments), by Euclidean distance transform. "
        "The Draft EIS does not state its DEM resolution or road dataset."),
      P("<b>Revealed practice.</b> 10,443 FACTS timber harvest units in the same forests (6,782 completed since FY2001; 151,841 acres; regeneration-type and treatment-N/A records excluded) were run through the identical terrain and road pipeline, "
        "so roadless and harvested land are compared on the same footing."),
      P("<b>Hazard.</b> USGS slope-relief landslide susceptibility (Mirus et al. 2024) and the USGS preliminary Hurricane Helene landslide inventory, summarized on a 90 m grid for IRA versus other national forest land "
        "(FS Basic Ownership layer, so private inholdings are excluded). Rates carry exact Poisson intervals. "
        "<b>Water.</b> Forests to Faucets 2.0 (HUC12): population served by surface-water intakes located in each watershed containing at least 500 IRA acres, with sensitivity to that threshold and downstream tracing. "
        "All code is deterministic and archived (Section 8).")]

# ---------- 4 findings ----------
S += [PageBreak(), P("4. Findings", h1), P("4.1 Where the roadless land is, and how steep", h2),
      fig("figures/fig1_map.png", 6.6),
      P("Figure 1. Study area. Roadless acreage is concentrated in the George Washington and Jefferson, Pisgah-Nantahala, Monongahela and Cherokee forests.", cap)]
S += [P("Mean slope across roadless acres is 41%. Steepness varies by forest: Pisgah-Nantahala (76% of acres above 35%) and Cherokee (72%) are steepest, Allegheny (14%) and Monongahela (45%) least steep. "
        "Figure 2 compares roadless slopes with slopes of recently harvested units in each forest.")]
S += [fig("figures/fig2_slope_ecdf.png", 7.0),
      P("Figure 2. Cumulative slope distributions by forest. Pooling all harvest records is misleading because the Allegheny (93,000 harvested acres, mostly gentle) dominates; forest-specific comparison is used throughout.", cap),
      P("Roadless land is steeper than harvested land in every forest, but harvest has occurred on steep ground in several: since FY2001, 47% of harvested acres in the Pisgah-Nantahala, 42% in the Cherokee, 36% in the Monongahela and 18% in the GW&J were above 35% slope. "
        "Steepness alone is therefore a weak indicator of what the agency has treated in practice.")]

S += [P("4.2 The agency's operability screen applied to Appalachian roadless land", h2),
      fig("figures/fig3_operability_space.png", 6.7),
      P("Figure 3. Roadless acres in slope-by-road-distance space with Draft EIS class boundaries.", cap)]
tab = [["Forest", "Roadless acres", "Likely operable", "Complex", "Not operable", "Harvested since 2001, likely operable"]]
tab[0] = [Paragraph("<b>%s</b>" % x, ParagraphStyle("th", parent=cell, alignment=0 if i == 0 else 2)) for i, x in enumerate(tab[0])]
r = scr[scr.kind == "IRA"].set_index("group"); h = scr[scr.kind == "harvest_FY>=2001"].set_index("group")
for g in ["GW&J", "Pisgah-Nantahala", "Monongahela", "Cherokee", "Chattahoochee", "Allegheny", "Daniel Boone", "ALL"]:
    a = r.loc[g]
    tab.append(["All core forests" if g == "ALL" else g, f"{a['total']:,.0f}", f"{100*a.share_operable:.0f}%", f"{100*a.share_complex:.0f}%", f"{100*a.share_not_operable:.0f}%", f"{100*h.loc[g].share_operable:.0f}%"])
t = Table(tab, colWidths=[1.6 * inch, 1.0 * inch, 1.0 * inch, 0.8 * inch, 0.95 * inch, 1.65 * inch])
t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "Helvetica", 8.2), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.2), ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 8.2),
                       ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK), ("LINEABOVE", (0, -1), (-1, -1), 0.5, INK2),
                       ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f3f6fb")]), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
S += [t, P("Table 1. Screen results by forest (slope and road distance only; DEM-derived acres).", cap)]
sens = pd.read_csv("data/processed/agency_screen_sensitivity.csv")
S += [P("Two sensitivity checks matter for interpretation. First, the thresholds: lowering both slope limits by 10 points reduces the likely operable share to 20%, raising them by 10 points increases it to 42%; "
        "shifting the distance limits by 0.25 mile gives 18% and 40%. Second, terrain resolution: 51.7% of roadless acres exceed 40% slope on a 10 m DEM, but 42.7% do on a 30 m DEM (6.8% versus 3.0% above 70%). "
        "Because the Draft EIS does not state its resolution, results derived from coarser terrain data would classify more land as operable than a 10 m analysis. "
        "I do not know which the agency used, which is why disclosure is requested.")]
S += [fig("figures/fig4_screen_by_forest.png", 6.9),
      P("Figure 4. Screen classes for roadless land and for land harvested since FY2001. Current roads are used for both; harvested land sits near roads partly because roads were built for harvest, so the harvested bars overstate how operable roadless land is. "
        "The comparison shows what the screen counts as ordinary working ground, not what future harvest would be.", cap),
      P("Read together, Figures 3 and 4 support a measured conclusion. Most roadless land here is <i>not</i> in the easiest class (69% is complex or not operable), so near-term harvest of all of it is implausible. "
        "But 86% is within the agency's operable or complex classes, and forest-level harvest history shows the agency has worked on steep ground in several forests. "
        "Whether the land is in fact harvested depends chiefly on forest-plan direction and market conditions, both of which can change.")]

S += [P("4.3 Landslide hazard", h2), fig("figures/fig5_hazard.png", 6.9),
      P("Figure 5. Left: Helene landslide density (95% Poisson interval). Right: USGS susceptibility per 90 m cell.", cap),
      P("Acre-weighted, 84% of the land in roadless areas is susceptible by the USGS slope-relief model versus 74% of other national forest land. In the Helene area (284,746 roadless acres versus 1,626,517 other acres), "
        "mapped landslides per 1,000 acres were 0.478 (n=136; 95% interval 0.401 to 0.565) versus 0.100 (n=163), 0.267 versus 0.049 for satellite-only detections, and 0.407 versus 0.076 excluding road- and building-impact points. "
        "The roughly fivefold difference is robust to these variants. It is confounded by rainfall gradients, slope, canopy and mapping effort, and the inventory is preliminary and incomplete. "
        "I read it as showing that these are hazardous slopes on which disturbance-related changes to drainage and soil deserve quantitative assessment, not as an estimate of the effect of roads or logging.")]

S += [P("4.4 Drinking water", h2), fig("figures/fig6_water.png", 6.9),
      P("Figure 6. Watersheds containing roadless land and the people served by intakes located in them.", cap),
      P(f"With a 500-acre threshold, {water['n_huc12_with_ira']} HUC12 watersheds contain roadless land and hold {int(water['sw_intakes_in_ira_huc12'])} surface-water intakes serving about {water['sum_pop_in_ira_huc12']/1000:,.0f},000 people; across six alternative definitions the range is 258,000 to 534,000. "
        f"Tracing five watersheds downstream reaches about {water['unique_sum_pop_in_or_downstream_hops_5']/1e6:.1f} million served (a lower bound because of clipping at the study extent); "
        "these people are served by intakes downstream and are not \"affected\" in any measured sense. The largest single watersheds are Mills River, NC (about 124,000 served; 18% roadless), Gap Creek-Watauga, TN (70,000) and North Indian Creek, NC/TN (66,000). "
        "For scale, the Draft EIS Table 35 reports 378 intakes serving 614,600 people for the whole Southern Region under Alternative 2."),
      P("<b>Wildfire context.</b> The Draft EIS (Table 22) reports high wildfire hazard potential on 7.1% of Southern Region and 5.4% of Eastern Region IRA acres versus 28.7% nationally, and notes that 94.5% of Southern Region IRA acres lie in the wildland-urban interface. "
        "By these measures the fire-hazard rationale for treatment in roadless areas looks less pronounced here than nationally, although the WUI share may matter under Alternative 3; the agency should present region-specific analysis.")]

# ---------- 5 limits ----------
S += [P("5. Limitations", h1),
      B("<b>Not a prediction of harvest.</b> The screen bounds what is physically accessible, not what would be sold. Forest-plan restrictions, productivity, markets and appeals are not modeled."),
      B("<b>Carbon and biodiversity are not assessed.</b> I did not have time to integrate forest carbon, habitat or species datasets at the rigor applied elsewhere in this comment. These are important, and I encourage others to analyze them for this region."),
      B("<b>Road data.</b> Current roads (TIGER and FS system roads) are used, including unclassified and decommissioned segments of uncertain status. Distance is Euclidean, not by travel route."),
      B("<b>Slope.</b> 10 m DEM slopes are sensitive to smoothing and lidar availability; the sensitivity to resolution is reported above."),
      B("<b>Hazard and water.</b> The Helene inventory is preliminary and biased toward mapped infrastructure impacts. Population served is by intake location, not a measure of exposure. Roadless watersheds differ from other watersheds in many ways."),
      B("<b>Scope.</b> Seven forest groupings only. Other Appalachian forests are excluded, and results say nothing about other regions.")]

# ---------- 6 requests ----------
S += [P("6. Requests to the agency", h1),
      P("The following are analytic gaps that would improve the record for decision-makers regardless of the alternative selected."),
      B("Report Alternative 2 and 3 results separately for the Eastern and Southern regions, and by national forest, including acres in each operability class after applying forest-plan restrictions."),
      B("Disclose the operability method and inputs: DEM source and resolution, road layer and vintage, treatment of decommissioned and unauthorized roads, and productivity data; and provide a sensitivity analysis (my results move 20 to 42% with threshold changes alone)."),
      B("Quantify landslide and debris-flow risk for the Appalachian forests, given steep, susceptible terrain, recent events, and the density difference described above, and compare road-related and other disturbance pathways."),
      B("Quantify drinking-water exposure for Appalachian watersheds (intakes, populations, treatment costs) at HUC12 or finer resolution, with downstream tracing."),
      B("Analyze plan-amendment exposure: for each forest, how much operable land is currently restricted only by plan direction that could be amended, and over what timeframe."),
      B("Provide the underlying geospatial layers used for the operability classification so that independent replication is possible.")]

# ---------- 7 conclusion ----------
S += [P("7. Conclusion", h1),
      P("In the core Appalachian forests, roadless land is steeper and more remote than harvested land, but terrain and distance leave most of it within the agency's operable or complex classes, "
        "sits on failure-prone ground, and lies in watersheds serving hundreds of thousands of people. The Draft EIS does not present evidence at a scale that lets a reader assess these facts for the region. "
        "The requests above would allow that assessment.")]

# ---------- 8 reproducibility ----------
S += [P("8. Reproducibility", h1),
      P("All code, derived tables, figure scripts and a manifest of source URLs and SHA-256 hashes are in the accompanying open repository [repository URL]. "
        "Running <font face='Courier'>make_all.sh</font> downloads the public inputs and regenerates every number and figure in this comment. Agency PDFs must be saved manually from Regulations.gov. "
        "The DEIS Vol. I (FS-2025-0001-224064) and Economic Analysis (FS-2025-0001-224067) were used as posted; hashes are in the manifest.")]

S += [P("9. References", h1)]
refs = ["USDA Forest Service (2025). Draft Environmental Impact Statement, Rescission of the Roadless Area Conservation Rule, Vol. I; Economic Analysis. Docket FS-2025-0001, Regulations.gov.",
        "USDA Forest Service Enterprise Data Warehouse. Inventoried Roadless Areas (2001); Administrative Forest Boundaries; Basic Ownership; Road Core; FACTS Timber Harvest; Forests to Faucets 2.0.",
        "U.S. Geological Survey. 3D Elevation Program 1/3 arc-second DEM; The National Map transportation (TIGER-derived) roads.",
        "Mirus, B. B., et al. (2024). Slope-relief landslide susceptibility for the conterminous United States (n10 model). U.S. Geological Survey, ScienceBase item 65ccea5bd34ef4b119cb3bac.",
        "USGS (2024). Preliminary landslide inventory for Hurricane Helene, ScienceBase item 674634a1d34e6d1dac3abddc.",
        "Horn, B. K. P. (1981). Hill shading and the reflectance map. Proc. IEEE 69(1): 14-47."]
S += [P(x, small) for x in refs]
doc.build(S)
print("built", OUT)
