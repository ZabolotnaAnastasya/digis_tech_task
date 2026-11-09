"""Спільні утиліти для всіх нотбуків: читання даних, назви колонок, Фур'є."""
import numpy as np, pandas as pd
from pathlib import Path

# common.py лежить у digis/notebooks → корінь проєкту на рівень вище
ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR  = DATA_DIR / "processed"          # сюди пише 02_data_prep
SHEET    = "Daily Data"


def find_data():
    """Шукає data/MMM_Candidate_Brief*.xlsx (витримує суфікси на кшталт «(1)»)."""
    f = sorted(DATA_DIR.glob("MMM_Candidate_Brief*.xlsx"))
    assert f, f"У {DATA_DIR} немає MMM_Candidate_Brief*.xlsx"
    return f[0]

# внутрішнє ім'я -> назва в Excel
COL = dict(
    date="Date", sales_inc="Sales including tax (£)", sales_ex="Sales excluding tax (£)",
    buyers="Purchasing customers", orders="Orders", new="New customers",
    bing="Bing spend (£)", google="Google Search spend (£)", meta="Meta spend (£)",
    pinterest="Pinterest spend (£)", spend_total="Total marketing spend (£)",
    promo="Promotion discount (%)", bf="Black Friday flag", cm="Cyber Monday flag",
    window="BF / Cyber Monday window flag")
CH = ["bing", "google", "meta", "pinterest"]
TAX = 0.20
TARGET_CAC = 40


def load(path=None, sheet=SHEET) -> pd.DataFrame:
    raw = pd.read_excel(path or find_data(), sheet_name=sheet)
    missing = [v for v in COL.values() if v not in raw.columns]
    assert not missing, f"Немає колонок: {missing}"
    df = raw.rename(columns={v: k for k, v in COL.items()})[list(COL)].copy()
    if pd.api.types.is_numeric_dtype(df["date"]):          # Excel-серіали
        df["date"] = pd.to_datetime(df["date"], unit="D", origin="1899-12-30")
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def fourier(k, x, period=365.25, tag="y"):
    """Пари sin/cos для гармонік 1..k. x — числовий індекс (наприклад day-of-year)."""
    return pd.DataFrame({f"{tag}_{f}{i}": g(2*np.pi*i*x/period)
                         for i in range(1, k+1) for f, g in (("s", np.sin), ("c", np.cos))})


def bf_cm_peak(df):
    """1 для днів від Black Friday до Cyber Monday включно (по кожному року)."""
    out = pd.Series(0, index=df.index)
    for y in df.date.dt.year.unique():
        b = df.loc[(df.bf == 1) & (df.date.dt.year == y), "date"]
        c = df.loc[(df.cm == 1) & (df.date.dt.year == y), "date"]
        if len(b) and len(c):
            out[df.date.between(b.iloc[0], c.iloc[0])] = 1
    return out


# ---------------------------------------------------------------------------
# Побудова MMM (спільна для тюнінгу та фінальної моделі).
# pymc_marketing імпортуємо всередині функції, щоб 01/02 працювали без нього.
# ---------------------------------------------------------------------------
OPTIONAL_CONTROLS = {                         # набори прапорців BF (див. 02_data_prep)
    "peak":               [],
    "peak+window":        ["bf_window"],
    "peak+window+bf+cm":  ["bf_window", "bf_day", "cm_day"],
}


def make_mmm(channels, controls, k_yearly=3, l_max=14, saturation="logistic",
             beta_sigma=0.5, tight_priors=True):
    """MMM із геометричним adstock. tight_priors=True — пріори, масштабовані під ціль 0..1
    (дефолтні дають prior-прогноз у тисячах клієнтів/день: див. prior predictive у 04)."""
    from pymc_marketing.mmm import MMM, GeometricAdstock, LogisticSaturation, HillSaturation
    from pymc_extras.prior import Prior
    sat_cls = {"logistic": LogisticSaturation, "hill": HillSaturation}[saturation]
    sat = sat_cls(priors={"beta": Prior("HalfNormal", sigma=beta_sigma, dims="channel")})
    cfg = None
    if tight_priors:
        cfg = {"likelihood":    Prior("Normal", sigma=Prior("HalfNormal", sigma=0.05), dims="date"),
               "intercept":     Prior("Normal", mu=0.2, sigma=0.1),
               "gamma_control": Prior("Normal", mu=0, sigma=0.3, dims="control"),
               "gamma_fourier": Prior("Laplace", mu=0, b=0.1, dims="fourier_mode")}
    return MMM(date_column="date", channel_columns=list(channels), target_column="new",
               control_columns=list(controls), adstock=GeometricAdstock(l_max=int(l_max)),
               saturation=sat, yearly_seasonality=int(k_yearly), model_config=cfg)
