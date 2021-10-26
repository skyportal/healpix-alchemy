import matplotlib.pyplot as plt
import json

with open('output.json') as f:
    data = json.load(f)

def data_list_to_dict(data):
    result_dict = {}
    for test_run in data['benchmarks']:
        test = test_run['fullname'].split('[')[0]
        if test in result_dict.keys():
            result_dict[test].append(test_run)
        else:
            result_dict[test] = [test_run]
    return result_dict

def runtime_plot(benchmark_list):
    N_list = [int(run['param']) for run in benchmark_list]
    t_list = [float(run['stats']['mean']) for run in benchmark_list]
    t_err = [float(run['stats']['stddev']) for run in benchmark_list]
    test = benchmark_list[0]['fullname'].split('[')[0].split('::')[1]
    fig, ax = plt.subplots()
    ax.errorbar(N_list, t_list, yerr = t_err, fmt = 'o')
    ax.set_xlabel('N')
    ax.set_ylabel('Runtime (s)')
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_title(test + ' Runtime Plot')
    plt.savefig(test + ' runtime plot')

benchmark_list = data_list_to_dict(data)
for test in benchmark_list:
    runtime_plot(benchmark_list[test])