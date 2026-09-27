"""Shared figure style. Palette = validated categorical slots 1-3 (blue, orange, aqua) from the reference data-viz palette;
ordinal 3-class ramp = single-hue blue steps (250/400/600). Text uses ink tokens, never series colors."""
import matplotlib as mpl
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
INK3 = "#8a8985"
GRID = "#e6e5e1"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
RAMP = {"operable": "#184f95", "complex": "#3987e5", "not_operable": "#9ec5f4"}   # dark = most loggable
FOREST_ORDER = ["GW&J", "Pisgah-Nantahala", "Monongahela", "Cherokee", "Chattahoochee", "Allegheny", "Daniel Boone"]


def apply():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.labelcolor": INK2,
        "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": INK3, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
        "xtick.major.width": 0.8, "ytick.major.width": 0.8, "legend.frameon": False,
        "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlelocation": "left",
    })


def footer(fig, text, y=0.012):
    fig.text(0.012, y, text, fontsize=6.5, color=INK3, ha="left", va="bottom")
