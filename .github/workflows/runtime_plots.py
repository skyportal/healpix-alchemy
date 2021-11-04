import json

import matplotlib.pyplot as plt
import pandas as pd

with open('benchmark_results.json') as f:
    data = json.load(f)

df = pd.json_normalize(data['benchmarks'])
df['func'] = df['name'].str.split('[', expand=True)[0]
df['fullfunc'] = df['fullname'].str.split('[', expand=True)[0]
df['param'] = pd.to_numeric(df['param'])
for func, group in df.groupby('func'):
    fig, ax = plt.subplots()
    group.plot.scatter(x='param', y='stats.mean', yerr='stats.stddev',
                       loglog=True, xlabel='N', ylabel='Runtime (s)', ax=ax)
    fig.tight_layout()
    fig.savefig(f'plots/{func}')
