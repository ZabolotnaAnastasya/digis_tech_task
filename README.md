# **MMM for E-commerce: New Customer Forecast and Spend Scenarios**

A Marketing Mix Model (PyMC-Marketing) that answers the brief's question: where should spend on Bing, Google Search, Meta and Pinterest increase or decrease to acquire new customers below **£40 per additional customer**? The starting point is average daily spend in September 2026\. The horizon is 30 days under similar trading conditions.

The data are synthetic. The field guide describes a fictional UK e-commerce brand with 730 days of data, from 1 October 2024 to 30 September 2026\.

## **Project Structure**

```
digis/
├── data/
│   ├── MMM_Candidate_Brief.xlsx          # input data (sheet "Daily Data")
│   └── processed/                         # created by notebooks 2–4
│       ├── model_input.csv                # 2: feature matrix for the model
│       ├── config.json                    # 2: column roles, controls, hold-out, baseline spend
│       ├── best_params.json               # 3: selected hyperparameters
│       ├── optuna_trials.csv              # 3: all tuning trials
│       ├── mmm_final.nc                   # 4: fitted model (posterior)
│       └── model_meta.json                # 4: parameters, sampler settings, hold-out metrics
└── notebooks/
    ├── common.py                          # shared utilities: data loading, column names, Fourier terms, make_mmm
    ├── 1_data_inspect.ipynb               # data exploration
    ├── 2_data_prep.ipynb                  # features, holiday flag selection, saving outputs
    ├── 3_tuning.ipynb                     # Optuna: cross-validation + independent hold-out
    ├── 4_modeling.ipynb                   # final model, diagnostics, interpretation
    └── 5_scenarios.ipynb                  # spend scenarios, marginal CAC,recommendation
```

Presentation Mapping

| Slide | Content | Notebook |
| :---- | :---- | :---- |
| 1 | Data inspection | 1\_data\_inspect |
| 2 | Data preparation | 2\_data\_prep |
| 3 | Hyperparameter tuning | 3\_tuning |
| 4 | Bayesian MMM: fit, validation, steady-state efficiency | 4\_modeling |
| 5 | Scenarios: five spend plans | 5\_scenarios |
| 6 | Limits and open questions | 4\_modeling, 5\_scenarios |

## **Run Order**

Run in Google Colab (or locally), in this order:

1. **1\_data\_inspect:** checks the file for missing values, duplicates and units.  
2. **2\_data\_prep:** creates `model_input.csv` and `config.json`. Required before 3–5.  
3. **3\_tuning:** optional, takes up to 45 minutes (time limit set in code). Without it, 4\_modeling uses default hyperparameters (k\_yearly=3, l\_max=14, logistic, beta\_sigma=0.5).  
4. **4\_modeling:** final model on all 730 days with full MCMC (4 chains × 1,000 draws). Creates `mmm_final.nc` and `model_meta.json`. Required before 5\.  
5. **5\_scenarios:** scenarios and recommendation. Reads the outputs of 2–4.

**Paths:** each notebook has a `PROJECT_DIR` cell. In Colab it points to `/content/drive/MyDrive/digis`. For local runs, uncomment `PROJECT_DIR = "."`.

**Library version:** pymc-marketing 1.3.0 (pinned in 3, 4 and 5). Other versions may change posterior variable names and method signatures.

## **Results (Current Full Run)**

* **Tuning:** k\_yearly=6, l\_max=21, logistic saturation, beta\_sigma=0.55, bf\_features=peak+window. Cross-validation MAPE 11.4% → 8.2%. Hold-out MAPE 9.2% → 7.2% (default → tuned).  
* **Final model convergence:** 0 divergences, max R-hat 1.008, minimum bulk ESS 782\.  
* **Hold-out (last 90 days, no Black Friday or holiday events):** MAPE 7.4% vs 12.4% for a weekday-naive forecast.  
* **Contribution:** media explains 49% of new customers, baseline 49%, controls about 1%.  
* **Marginal CAC at September 2026 spend (steady state, median):** Bing £10, Pinterest £26, Meta £29, Google £43.  
* **30-day scenarios (new customers, median and 5th–95th percentile):**  
  * All channels \+10%: \+576 (505 to 648), incremental CAC £30  
  * All channels \+20%: \+1,143 (1,004 to 1,287), incremental CAC £30  
  * All channels −10%: −584 (−658 to −510), saves £29.5 per customer lost  
  * Optimised reallocation at constant budget (Bing \+20%, Pinterest \+20%, Meta \+10%, Google −20%): \+272 (132 to 406\)  
* **Google \+10% alone:** incremental CAC £44, P(below £40) \= 27%.

**Recommendation:** Scale Bing and Meta and reduce Google at the margin. Pinterest is a borderline scale candidate (P \= 89%). Validate the Google-to-other-channel shift with a geo or matched-market test before any permanent budget change. Scale only if the measured incremental CAC stays below £40 with at least 80% confidence.

Figures come from a full run of 4\_modeling and 5\_scenarios in Colab. Check them against the notebook output before reusing them.

## **How to Read the Results**

* **Target:** new customers. Sales, orders and purchasing customers are consequences of advertising, so they are excluded from the model to prevent leakage.  
* **Marginal CAC:** Δspend / Δcustomers for an additional pound. It is compared with £40. The average CAC of a channel (total spend / customers) is not used for decisions.  
* **Ranges:** 5th–95th percentile of the posterior distribution. They reflect parameter uncertainty, not an exact forecast.  
* **P(iCPA \< £40):** share of posterior draws in which additional customers cost less than £40.  
* **Decision rule (proposed):** scale when P ≥ 80%; hold or test when 50–80%; reduce at the margin when the probability is low.

  ## **Validation Status**

* The scenario engine in 5\_scenarios matches the library's `sample_posterior_predictive` on the same posterior draws, for both logistic and Hill saturation, to machine precision.  
* A hand calculation for a single channel matches the engine to machine precision.  
* Marginal CAC in closed form matches a numerical derivative (relative error below 1e-4).  
* Sensitivity: 8 reliable specifications (lag length, seasonality order, saturation form, prior scale, event flags). Default library priors are excluded because sampling was unreliable (R-hat 1.018, ESS 163).

  ## **Limitations**

* **Priors:** the prior predictive check passes with a warning. The observed mean (433 customers per day) falls outside the 90% prior interval (525 to 2,725), so the priors are centred too high.  
* **Carry-over:** half-life is under one day for all channels. For Google, Meta and Pinterest, the posterior is only partly updated from the prior. Delayed effects are therefore not established, although the brief asks for them.  
* **Google saturation:** the posterior is wider than the prior (ratio 1.6), a sign of weak identification.  
* **Events:** only two Black Friday and Cyber Monday periods in the data. Black Friday and Cyber Monday are under-predicted by 15–18%, and Black Friday weekend is over-predicted by about 26%.  
* **Seasonality:** yearly seasonality is estimated from two cycles.  
* **Bing:** the recommendation to scale Bing relies on spend changes of ×2 to ×6 that have not yet been confirmed with the client. They could be tracking errors.  
* **Reallocation:** sensitivity was tested for ±10% and ±20% steps per channel. The full reallocation has not yet been re-run under alternative specifications.  
* **Halloween:** significant in exploratory analysis (p \= 0.001) but not included in the model. The reason is not documented.  
* **No media-free benchmark:** the value of advertising beyond calendar effects is not yet proven against a model with no media.  
* **Causality:** good prediction does not prove that advertising caused the additional customers. A geo or matched-market test is required to confirm causal effects.

  ## **Dependencies**

`pymc-marketing==1.3.0`, `arviz`, `openpyxl`, `pandas`, `numpy`, `scipy`, `statsmodels`, `optuna`, `scikit-learn`, `matplotlib`. Notebooks 3 and 4 install the required packages automatically in Colab.

Colab may show a dependency warning about `tensorflow` and `h5py`. It does not affect results. If imports fail after installation, restart the session and run the notebook again.

&nbsp;