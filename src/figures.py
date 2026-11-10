"""Generate figures from source-reported datasets and derived model outputs.

Run from any directory: python src/figures.py
This script does not fabricate experimental values or overwrite source CSVs.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'processed'
REPORTS = ROOT / 'reports'
FIG = REPORTS / 'figures'
FIG.mkdir(parents=True, exist_ok=True)


def read_formulations():
    file = DATA / 'gelma_source_formulations.csv'
    if not file.exists():
        raise FileNotFoundError(f'Missing {file}. Run python src/reproduce.py first or restore the source CSV.')
    df = pd.read_csv(file)
    required = {'GelMA_concentration_pct', 'curing_time_s', 'mean_modulus_kPa'}
    if not required.issubset(df.columns):
        raise ValueError(f'{file} missing columns: {sorted(required - set(df.columns))}. Found: {list(df.columns)}')
    df = df.sort_values(['GelMA_concentration_pct', 'curing_time_s']).copy()
    if len(df) != 12 or df[['GelMA_concentration_pct','curing_time_s']].duplicated().any():
        raise ValueError('Expected precisely 12 unique GelMA formulation conditions')
    if (df.mean_modulus_kPa <= 0).any():
        raise ValueError('Reported modulus must be positive')
    return df


def style():
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False,
        'axes.labelsize': 11, 'axes.titlesize': 13, 'figure.dpi': 140,
        'savefig.dpi': 300,
    })


def save(fig, name):
    fig.savefig(FIG / f'{name}.png', dpi=300, bbox_inches='tight', facecolor='white')
    fig.savefig(FIG / f'{name}.pdf', bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('Saved:', FIG / f'{name}.png')


def formulation_plot(df):
    fig, ax = plt.subplots(figsize=(8.2,4.6))
    for concentration, subset in df.groupby('GelMA_concentration_pct'):
        s = subset.sort_values('curing_time_s')
        yerr = s['std_modulus_kPa'] if 'std_modulus_kPa' in s.columns else None
        ax.errorbar(s.curing_time_s, s.mean_modulus_kPa,
                    yerr=yerr, fmt='o-', linewidth=2, markersize=6,
                    capsize=3, label=f'{int(concentration)}% GelMA')
    ax.set_xticks([30, 60, 90, 120])
    ax.set_xlabel('Curing time (s)')
    ax.set_ylabel('Source-reported mean modulus (kPa)')
    ax.set_title('GelMA stiffness across formulation conditions')
    ax.legend(frameon=False, ncol=3, loc='upper left')
    ax.grid(alpha=.22, axis='y')
    fig.text(.11,.005,'Error bars: specimen SD where available; descriptive, not independent-batch uncertainty.',fontsize=8)
    save(fig,'01_formulation_stiffness')


def heatmap(df):
    matrix = df.pivot(index='GelMA_concentration_pct',columns='curing_time_s',values='mean_modulus_kPa')
    fig, ax = plt.subplots(figsize=(7.7,4))
    im = ax.imshow(matrix.values, aspect='auto', cmap='viridis')
    ax.set_xticks(range(matrix.shape[1]), [f'{x}s' for x in matrix.columns])
    ax.set_yticks(range(matrix.shape[0]), [f'{int(x)}%' for x in matrix.index])
    ax.set_xlabel('Curing time'); ax.set_ylabel('GelMA concentration')
    ax.set_title('Measured formulation-level modulus (kPa)')
    for (row, col), val in np.ndenumerate(matrix.values):
        ax.text(col,row,f'{val:.1f}',ha='center',va='center',
                color='white' if im.norm(val)<.55 else 'black',fontweight='bold')
    fig.colorbar(im,ax=ax,label='Mean modulus (kPa)',fraction=.045,pad=.04)
    save(fig,'02_formulation_heatmap')


def prediction_plot(df):
    file = DATA / 'source_loocv_predictions.csv'
    if not file.exists():
        print('Skipped predictions: missing', file, '(run python src/reproduce.py)')
        return
    pred = pd.read_csv(file)
    target = 'mean_modulus_kPa'
    model = 'Log-target Quadratic Ridge'
    if not {target,model}.issubset(pred.columns):
        raise ValueError(f'Prediction table missing {target} or {model}')
    actual, predicted = pred[target].to_numpy(),pred[model].to_numpy()
    fig, ax = plt.subplots(figsize=(6.3,5.2))
    ax.scatter(actual,predicted,s=72,alpha=.85,edgecolors='white',linewidths=.8)
    lo,hi=min(actual.min(),predicted.min()),max(actual.max(),predicted.max())
    ax.plot([lo,hi],[lo,hi],linestyle='--',color='black',lw=1.2,label='Perfect prediction')
    for _,row in pred.iterrows():
        if {'GelMA_concentration_pct','curing_time_s'}.issubset(pred.columns):
            ax.annotate(f"{int(row.GelMA_concentration_pct)}%/{int(row.curing_time_s)}s",
                        (row[target],row[model]),xytext=(4,5),textcoords='offset points',fontsize=7)
    mae=np.mean(np.abs(actual-predicted));rmse=np.sqrt(np.mean((actual-predicted)**2))
    r2=1 - np.sum((actual-predicted)**2)/np.sum((actual-actual.mean())**2)
    ax.text(.04,.96,f'LOOCV  |  MAE {mae:.2f} kPa  |  RMSE {rmse:.2f} kPa  |  R² {r2:.3f}',
            transform=ax.transAxes,va='top',fontsize=9,
            bbox=dict(boxstyle='round,pad=.4',facecolor='white',edgecolor='0.85'))
    ax.set_xlabel('Source-reported mean modulus (kPa)')
    ax.set_ylabel('Predicted mean modulus (kPa)')
    ax.set_title('Leave-one-formulation-out prediction')
    ax.legend(frameon=False,loc='lower right')
    ax.grid(alpha=.2)
    save(fig,'03_loocv_predictions')


def benchmark_plot():
    candidates=[DATA/'source_active_learning_summary.csv',
                REPORTS/'final_active_learning_summary.csv',
                REPORTS/'source_active_learning_summary.csv']
    existing=next((x for x in candidates if x.exists()),None)
    if existing is None:
        print('Skipped acquisition figure: no benchmark summary found')
        return
    summary=pd.read_csv(existing)
    def find(options):
        return next((c for c in options if c in summary.columns),None)
    strategy=find(['strategy','Strategy','policy','Policy'])
    mean=find(['mean_experiments','mean_total_experiments','mean_total','mean_trials','Mean total experiments'])
    if not strategy or not mean:
        print('Benchmark columns:',list(summary.columns))
        raise ValueError(f'Could not identify strategy/mean-experiment columns in {existing}')
    vals=summary[[strategy,mean]].copy()
    vals[strategy]=vals[strategy].astype(str)
    vals[mean]=pd.to_numeric(vals[mean],errors='raise')
    order=['GPR-UCB','Greedy','Random (expected)','Uncertainty']
    vals['order']=vals[strategy].map({s:i for i,s in enumerate(order)}).fillna(99)
    vals=vals.sort_values(['order',strategy]);
    fig,ax=plt.subplots(figsize=(7.8,4.4))
    colors=['#147d80' if 'UCB' in s else '#6993b8' if 'Greedy' in s else '#a4aab6' if 'Random' in s else '#d7a66b' for s in vals[strategy]]
    bars=ax.barh(vals[strategy],vals[mean],color=colors,height=.62)
    ax.invert_yaxis();ax.bar_label(bars,fmt='%.2f',padding=4)
    ax.set_xlim(0,max(vals[mean])*1.19)
    ax.set_xlabel('Mean total formulation evaluations (lower is better)')
    ax.set_title('Retrospective active-learning benchmark')
    ax.grid(alpha=.17,axis='x');ax.set_axisbelow(True)
    fig.text(.11,.006,f'Source: {existing.relative_to(ROOT)}. Fixed 12-formulation candidate set; not prospective experiments.',fontsize=8)
    save(fig,'04_active_learning_benchmark')


def main():
    style();df=read_formulations()
    formulation_plot(df);heatmap(df);prediction_plot(df);benchmark_plot()
    print('\nSource-reported figures saved to',FIG)

if __name__=='__main__':main()
