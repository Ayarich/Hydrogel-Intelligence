"""Independent source-reported GelMA formulation analysis.

Requires data/raw/GelMA_Characterization_Data.xlsx from the cited Mendeley dataset.
Does not silently overwrite raw data or represent retrospective simulations as lab tests.
"""
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/GelMA_Characterization_Data.xlsx'
OUT = ROOT / 'data/processed'
OUT.mkdir(parents=True, exist_ok=True)


def load_source():
    if not RAW.exists():
        raise FileNotFoundError(f'Download the source workbook into {RAW}')
    raw = pd.read_excel(RAW, sheet_name='YoungsModulus', header=None)
    rows = []
    for row_i, (concentration, curing_time) in enumerate(
        [(c,t) for c in [10,15,20] for t in [30,60,90,120]], start=4
    ):
        for specimen, value in enumerate(raw.iloc[row_i, 2:14], start=1):
            rows.append({'GelMA_concentration_pct': concentration,
                         'curing_time_s': curing_time,
                         'specimen_number': specimen,
                         'reported_modulus_kPa': pd.to_numeric(value, errors='coerce')})
    specimens = pd.DataFrame(rows)
    if len(specimens) != 144 or specimens.reported_modulus_kPa.isna().any():
        raise ValueError('Unexpected source worksheet structure')
    means = specimens.groupby(['GelMA_concentration_pct','curing_time_s'], as_index=False).agg(
        mean_modulus_kPa=('reported_modulus_kPa','mean'),
        std_modulus_kPa=('reported_modulus_kPa','std'),
        specimen_count=('reported_modulus_kPa','size'))
    specimens.to_csv(OUT/'gelma_source_specimens.csv', index=False)
    means.to_csv(OUT/'gelma_source_formulations.csv', index=False)
    return means


def modeling(df):
    X = df[['GelMA_concentration_pct','curing_time_s']]
    y = df['mean_modulus_kPa']
    models = {
        'Mean baseline': DummyRegressor(strategy='mean'),
        'Log-target Quadratic Ridge': TransformedTargetRegressor(
            regressor=make_pipeline(StandardScaler(),
                                    PolynomialFeatures(2, include_bias=False),
                                    Ridge(alpha=1.0)),
            func=np.log, inverse_func=np.exp)
    }
    scores = []
    predictions = df.copy()
    for name, model in models.items():
        pred = cross_val_predict(model, X, y, cv=LeaveOneOut())
        predictions[name] = pred
        scores.append({'Model':name,'MAE_kPa':mean_absolute_error(y,pred),
                       'RMSE_kPa':np.sqrt(mean_squared_error(y,pred)),
                       'LOOCV_R2':r2_score(y,pred)})
    pd.DataFrame(scores).to_csv(OUT/'source_model_metrics.csv', index=False)
    predictions.to_csv(OUT/'source_loocv_predictions.csv', index=False)
    return pd.DataFrame(scores)


def search_benchmark(df):
    X = df[['GelMA_concentration_pct','curing_time_s']].to_numpy()
    y = df.mean_modulus_kPa.to_numpy()
    best_idx = int(np.argmax(y))

    def select_next(observed, strategy):
        remaining = [i for i in range(len(y)) if i not in observed]
        scaler=StandardScaler()
        xtr=scaler.fit_transform(X[observed])
        xte=scaler.transform(X[remaining])
        log_y=np.log(y[observed]); center=log_y.mean()
        kernel=ConstantKernel(1.0,constant_value_bounds='fixed')*Matern(
            length_scale=[1.0,1.0],length_scale_bounds='fixed',nu=2.5)
        gp=GaussianProcessRegressor(kernel=kernel,alpha=0.005,optimizer=None,normalize_y=False)
        gp.fit(xtr,log_y-center)
        mu, sd=gp.predict(xte,return_std=True)
        if strategy=='Greedy':scores=mu+center
        elif strategy=='Uncertainty':scores=sd
        elif strategy=='GPR-UCB':scores=mu+center+sd
        else:raise ValueError(strategy)
        return remaining[int(np.argmax(scores))]

    records=[]
    for initial in combinations(range(len(y)),3):
        if best_idx in initial:continue
        for strategy in ['Greedy','Uncertainty','GPR-UCB']:
            observed=list(initial)
            while best_idx not in observed:
                observed.append(select_next(observed,strategy))
            records.append({'initial':str(initial),'strategy':strategy,'experiments':len(observed)})
    out=pd.DataFrame(records)
    out.to_csv(OUT/'source_active_learning_runs.csv',index=False)
    summary=out.groupby('strategy',as_index=False).agg(
        mean_experiments=('experiments','mean'),
        median_experiments=('experiments','median'),
        success_by_5=('experiments',lambda s:(s<=5).mean()),
        success_by_6=('experiments',lambda s:(s<=6).mean()))
    summary=pd.concat([summary,pd.DataFrame([{
        'strategy':'Random (expected)','mean_experiments':8.0,
        'median_experiments':8.0,'success_by_5':2/9,'success_by_6':3/9
    }])],ignore_index=True)
    summary.to_csv(OUT/'source_active_learning_summary.csv',index=False)
    return summary


if __name__=='__main__':
    df=load_source()
    print('\nSOURCE-REPORTED MODEL EVALUATION\n',modeling(df).round(3).to_string(index=False))
    print('\nRETROSPECTIVE EXPERIMENT SEARCH\n',search_benchmark(df).round(3).to_string(index=False))
    print('\nOutputs saved under', OUT)
