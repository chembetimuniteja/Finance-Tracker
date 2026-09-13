import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="white")

# One consistent categorical palette, reused everywhere a category needs a
# color (dashboard donut, reports ranking) so a category always reads the
# same way across the app.
CAT_PALETTE = [
    "#2BB693",
    "#5B9BD9",
    "#E3A23D",
    "#B47EE5",
    "#E2685A",
    "#4FB477",
    "#D98BC0",
    "#7C93C9",
    "#C9A227",
    "#8FA6AD",
]


def _style_axes(fig, ax, theme):
    fig.patch.set_facecolor(theme["surface"])
    ax.set_facecolor(theme["surface"])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=theme["text_muted"], labelsize=9, length=0)


def _empty_state(fig, ax, message, theme):
    ax.text(
        0.5, 0.5, message, ha="center", va="center",
        color=theme["text_muted"], fontsize=12, transform=ax.transAxes,
    )
    ax.axis("off")


def category_donut(breakdown, theme, figsize=(4.8, 4.0)):
    """Donut chart of expense-by-category for one month, with the total
    spent shown in the center."""
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    fig.patch.set_facecolor(theme["surface"])

    if breakdown.empty:
        _empty_state(fig, ax, "No expenses logged\nfor this month yet", theme)
        return fig

    values = breakdown.values
    labels = breakdown.index.tolist()
    colors = [CAT_PALETTE[i % len(CAT_PALETTE)] for i in range(len(labels))]

    wedges, _ = ax.pie(
        values,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.38, "edgecolor": theme["surface"], "linewidth": 3},
    )
    total = values.sum()
    ax.text(0, 0.08, f"${total:,.0f}", ha="center", va="center",
            fontsize=17, fontweight="bold", color=theme["text"])
    ax.text(0, -0.16, "this month", ha="center", va="center",
            fontsize=8.5, color=theme["text_muted"])
    ax.axis("equal")

    ax.legend(
        wedges,
        [f"{label}   ${value:,.0f}" for label, value in zip(labels, values)],
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        frameon=False,
        fontsize=8.5,
        labelcolor=theme["text"],
        handlelength=1.1,
        handleheight=1.1,
    )
    # Fixed fractional margins rather than tight_layout(): the embedded
    # Tkinter frame is often narrower than `figsize` implies, and
    # tight_layout's margins are computed for the original size, so they
    # under-allocate room for the legend once TkAgg rescales the canvas.
    fig.subplots_adjust(left=0.02, right=0.48, top=0.95, bottom=0.05)
    return fig


def budget_bars(status_df, theme, figsize=(6.4, 4.2)):
    """Horizontal budget-vs-actual bars, one per category. Bar color turns
    amber near the limit and coral once it's exceeded."""
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    _style_axes(fig, ax, theme)

    if status_df.empty or status_df["limit"].sum() == 0 and status_df["spent"].sum() == 0:
        _empty_state(fig, ax, "No budgets set yet", theme)
        return fig

    df = status_df[(status_df["limit"] > 0) | (status_df["spent"] > 0)]
    df = df.sort_values("limit", ascending=True)
    y_pos = range(len(df))
    limits = df["limit"].values
    spent = df["spent"].values

    ax.barh(y_pos, limits, color=theme["border"], height=0.55, zorder=1, label="Budget")
    bar_colors = [
        theme["coral"] if (l > 0 and s > l) or (l == 0 and s > 0)
        else theme["amber"] if l > 0 and s / l > 0.85
        else theme["accent"]
        for s, l in zip(spent, limits)
    ]
    ax.barh(y_pos, spent, color=bar_colors, height=0.55, zorder=2, label="Spent")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(df["category"], color=theme["text"], fontsize=9.5)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.set_xlim(left=0)
    ax.grid(axis="x", color=theme["border"], linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    # Fixed left margin sized for the longest category label ("Health &
    # Fitness"), so it never gets clipped when TkAgg rescales the canvas
    # to a container narrower than `figsize`.
    fig.subplots_adjust(left=0.32, right=0.97, top=0.96, bottom=0.12)
    return fig


def trend_lines(trend_df, theme, figsize=(8.6, 3.6)):
    """Income vs. expenses across several months, with the surplus months
    lightly shaded."""
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    _style_axes(fig, ax, theme)

    if trend_df.empty or (trend_df["income"].sum() == 0 and trend_df["expense"].sum() == 0):
        _empty_state(fig, ax, "No activity in this period yet", theme)
        return fig

    x = range(len(trend_df))
    ax.plot(x, trend_df["income"], color=theme["blue"], marker="o", linewidth=2.2, label="Income")
    ax.plot(x, trend_df["expense"], color=theme["coral"], marker="o", linewidth=2.2, label="Expenses")
    ax.fill_between(
        x, trend_df["income"], trend_df["expense"],
        where=(trend_df["income"] >= trend_df["expense"]),
        color=theme["accent"], alpha=0.12, interpolate=True,
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(trend_df["label"], color=theme["text_muted"], fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.grid(axis="y", color=theme["border"], linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=theme["text"])
    fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.12)
    return fig
