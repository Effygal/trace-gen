import numpy as np
import trace_gen as tg
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput, Select
from bokeh.plotting import figure

MIN_EPS = 1e-6
M_MIN = 100
N_MIN = 10000
P_IRM_MIN = 0.0
MAX_K = 100


def fgen(k, indices, eps=1e-6):
    l = np.full(k, eps)  # Initialize all elements to eps
    s = len(indices)
    l[indices] = (1 - eps) / s  # Assign spike values
    l = l / l.sum()
    return np.arange(len(l)), l 

def gset(g, irm_type, zipf_a=None, pareto_a=None, pareto_xm=None, normal_mean=None, normal_std=None, uniform_a=None, uniform_b=None):
    if irm_type == 'zipf':
        g.set_zipf(zipf_a)
    elif irm_type == 'pareto':
        g.set_pareto(pareto_a, pareto_xm)
    elif irm_type == 'normal':
        g.set_normal(normal_mean, normal_std)
    elif irm_type == 'uniform':
        g.set_uniform(uniform_a, uniform_b)
    else:
        raise ValueError(f'Invalid g parameter.')

def mrc_compute(k, indices, eps, p_irm, M=100, n = 10000, irm_type=None, zipf_a=None, pareto_a=None, pareto_xm=None, normal_mean=None, normal_std=None, uniform_a=None, uniform_b=None):
    g = tg.TraceGenerator(M, n)
    if irm_type is not None:
        gset(g, irm_type, zipf_a, pareto_a, pareto_xm, normal_mean, normal_std, uniform_a, uniform_b)
    x, pdf = fgen(k, indices, eps)
    t, i, _ = g.gen_from_pdf(pdf, p_irm)
    M2 = len(set(t))
    K2 = M2 // 20
    c = np.arange(1, M2, K2)
    hr_lru = [tg.sim_lru(int(_c), t, raw=True) for _c in c]
    return c, hr_lru

# Initial values
indices = [1, 2]
eps = 5e-3 
MIN_K = max(indices) + 1
x, y = fgen(MIN_K, indices, eps)
p_irm = P_IRM_MIN
c, hr = mrc_compute(MIN_K, indices, eps, p_irm, M_MIN, N_MIN)

fgen_source = ColumnDataSource(data=dict(x=x, y=y))
mrc_source = ColumnDataSource(data=dict(c=c, hr=hr))

p = figure(title="f", width=350, height=350)
p.line(x='x', y='y', line_width=2, color='orange', source=fgen_source)

p2 = figure(title="MRC", width=350, height=350)
p2.line(x='c', y='hr', line_width=2, source=mrc_source)

indices_input = TextInput(
    value=str(indices), title="Spike indices"
)

eps_input = TextInput(
    value=str(eps), title="Epsilon"
)

p_irm_slider = Slider(
    title="p_irm", value=p_irm, start=0.0, end=1.0, step=0.01
)

M_select = Select(
    title="M", value="100", options=["100", "1000", "10000"]
)

k_slider = Slider(
    start=MIN_K, end=MAX_K, value=MIN_K, step=1, title="k parameter"
)

n_select = Select(
    title="n", value="10000", options=["10000", "100000", "1000000", "10000000"]
)

# Adding widgets for gset function parameters
irm_type_select = Select(title="IRM Type", value="zipf", options=["zipf", "pareto", "normal", "uniform"])
zipf_a_slider = Slider(title="Zipf a", value=1.2, start=1.0, end=10.0, step=0.1)
pareto_a_slider = Slider(title="Pareto a", value=2.5, start=1.0, end=10.0, step=0.1)
pareto_xm_slider = Slider(title="Pareto xm", value=0, start=0, end=int(M_select.value), step=1)
normal_mean_slider = Slider(title="Normal Mean", value=int(M_select.value)//2, start=0, end=int(M_select.value), step=1)
normal_std_slider = Slider(title="Normal Std", value=int(M_select.value)//6, start=0, end=int(M_select.value), step=1)
uniform_a_slider = Slider(title="Uniform a", value=0, start=0, end=int(M_select.value), step=10)
uniform_b_slider = Slider(title="Uniform b", value=int(M_select.value), start=int(uniform_a_slider.value), end=int(M_select.value), step=10)

# Initially hide all sliders
zipf_a_slider.visible = True
pareto_a_slider.visible = False
pareto_xm_slider.visible = False
normal_mean_slider.visible = False
normal_std_slider.visible = False
uniform_a_slider.visible = False
uniform_b_slider.visible = False

def update_k(attrname: str, old: int, new: int):
    print(f'old {attrname}: {old} -> {new}')
    assert isinstance(new, int) and new >= MIN_K and new <= int(M_select.value)
    x, y = fgen(new, eval(indices_input.value), eval(eps_input.value))
    fgen_source.data = dict(x=x, y=y)
    c, hr = mrc_compute(new, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value, int(M_select.value), int(n_select.value),
                        irm_type_select.value, zipf_a_slider.value, pareto_a_slider.value,
                        pareto_xm_slider.value, normal_mean_slider.value, normal_std_slider.value,
                        uniform_a_slider.value, uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

k_slider.on_change('value', update_k)

def update_indices(attrname: str, old: str, new: str):
    print(f'old {attrname}: {old} -> {new}')
    new_indices = eval(new)
    assert isinstance(new_indices, list)
    if max(new_indices) >= k_slider.value:
        k_slider.start = max(new_indices) + 1
        k_slider.value = max(new_indices) + 1
    x, y = fgen(k_slider.value, new_indices, eval(eps_input.value))
    fgen_source.data = dict(x=x, y=y)
    c, hr = mrc_compute(k_slider.value, new_indices, eval(eps_input.value), p_irm_slider.value, int(M_select.value), int(n_select.value),
                        irm_type_select.value, zipf_a_slider.value, pareto_a_slider.value,
                        pareto_xm_slider.value, normal_mean_slider.value, normal_std_slider.value,
                        uniform_a_slider.value, uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)
    

indices_input.on_change('value', update_indices)

def update_eps(attrname: str, old: str, new: str):
    print(f'old {attrname}: {old} -> {new}')
    new_eps = eval(new)   
    assert isinstance(new_eps, float) and new_eps >= 1e-10 and new_eps <= 1/k_slider.value
    x, y = fgen(k_slider.value, eval(indices_input.value), new_eps)
    fgen_source.data = dict(x=x, y=y)
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), new_eps, p_irm_slider.value,
                        int(M_select.value), int(n_select.value),
                        irm_type=irm_type_select.value, zipf_a=zipf_a_slider.value, pareto_a=pareto_a_slider.value,
                        pareto_xm=pareto_xm_slider.value, normal_mean=normal_mean_slider.value, normal_std=normal_std_slider.value,
                        uniform_a=uniform_a_slider.value, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

eps_input.on_change('value', update_eps)

def update_M(attrname: str, old: str, new: str):
    print(f'old {attrname}: {old} -> {new}')
    assert new in M_select.options and isinstance(int(new), int)
    pareto_xm_slider.end = int(new)
    normal_std_slider.end = int(new)
    normal_mean_slider.end = int(new)
    uniform_b_slider.end = int(new)
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value,
                        M=int(new), n=int(n_select.value),
                        irm_type=irm_type_select.value, zipf_a=zipf_a_slider.value, pareto_a=pareto_a_slider.value,
                        pareto_xm=pareto_xm_slider.value, normal_mean=normal_mean_slider.value, normal_std=normal_std_slider.value,
                        uniform_a=uniform_a_slider.value, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

M_select.on_change('value', update_M)

def update_n(attrname: str, old: str, new: str):
    print(f'old {attrname}: {old} -> {new}')
    assert new in n_select.options and isinstance(int(new), int)
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value,
                        M=int(M_select.value), n=int(new),
                        irm_type=irm_type_select.value, zipf_a=zipf_a_slider.value, pareto_a=pareto_a_slider.value,
                        pareto_xm=pareto_xm_slider.value, normal_mean=normal_mean_slider.value, normal_std=normal_std_slider.value,
                        uniform_a=uniform_a_slider.value, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

n_select.on_change('value', update_n)

def update_p_irm(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), new, int(M_select.value), int(n_select.value),
                        irm_type_select.value, zipf_a_slider.value, pareto_a_slider.value,
                        pareto_xm_slider.value, normal_mean_slider.value, normal_std_slider.value,
                        uniform_a_slider.value, uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

p_irm_slider.on_change('value', update_p_irm)

def update_irm_type(attrname: str, old: str, new: str):
    print(f'old {attrname}: {old} -> {new}')
    # Show or hide relevant sliders based on IRM type selection
    zipf_a_slider.visible = new == 'zipf'
    pareto_a_slider.visible = new == 'pareto'
    pareto_xm_slider.visible = new == 'pareto'
    normal_mean_slider.visible = new == 'normal'
    normal_std_slider.visible = new == 'normal'
    uniform_a_slider.visible = new == 'uniform'
    uniform_b_slider.visible = new == 'uniform'

    # Update data
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value,
                        M=int(M_select.value), n=int(n_select.value),
                        irm_type=new, zipf_a=zipf_a_slider.value, pareto_a=pareto_a_slider.value,
                        pareto_xm=pareto_xm_slider.value, normal_mean=normal_mean_slider.value, normal_std=normal_std_slider.value,
                        uniform_a=uniform_a_slider.value, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

irm_type_select.on_change('value', update_irm_type)

def update_zipf_a(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value,
                        M=int(M_select.value), n=int(n_select.value),
                        irm_type=irm_type_select.value, zipf_a=new, pareto_a=pareto_a_slider.value,
                        pareto_xm=pareto_xm_slider.value, normal_mean=normal_mean_slider.value, normal_std=normal_std_slider.value,
                        uniform_a=uniform_a_slider.value, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

zipf_a_slider.on_change('value', update_zipf_a)

def update_pareto_a(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value,
                        M=int(M_select.value), n=int(n_select.value),
                        irm_type=irm_type_select.value, zipf_a=zipf_a_slider.value, pareto_a=new,
                        pareto_xm=pareto_xm_slider.value, normal_mean=normal_mean_slider.value, normal_std=normal_std_slider.value,
                        uniform_a=uniform_a_slider.value, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

pareto_a_slider.on_change('value', update_pareto_a)

def update_pareto_xm(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value,
                        M=int(M_select.value), n=int(n_select.value),
                        irm_type=irm_type_select.value, zipf_a=zipf_a_slider.value, pareto_a=pareto_a_slider.value,
                        pareto_xm=new, normal_mean=normal_mean_slider.value, normal_std=normal_std_slider.value,
                        uniform_a=uniform_a_slider.value, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

pareto_xm_slider.on_change('value', update_pareto_xm)

def update_normal_mean(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value,
                        M=int(M_select.value), n=int(n_select.value),
                        irm_type=irm_type_select.value, zipf_a=zipf_a_slider.value, pareto_a=pareto_a_slider.value,
                        pareto_xm=pareto_xm_slider.value, normal_mean=new, normal_std=normal_std_slider.value,
                        uniform_a=uniform_a_slider.value, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

normal_mean_slider.on_change('value', update_normal_mean)

def update_normal_std(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value,
                        M=int(M_select.value), n=int(n_select.value),
                        irm_type=irm_type_select.value, zipf_a=zipf_a_slider.value, pareto_a=pareto_a_slider.value,
                        pareto_xm=pareto_xm_slider.value, normal_mean=normal_mean_slider.value, normal_std=new,
                        uniform_a=uniform_a_slider.value, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

normal_std_slider.on_change('value', update_normal_std)

def update_uniform_a(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value,
                        M=int(M_select.value), n=int(n_select.value),
                        irm_type=irm_type_select.value, zipf_a=zipf_a_slider.value, pareto_a=pareto_a_slider.value,
                        pareto_xm=pareto_xm_slider.value, normal_mean=normal_mean_slider.value, normal_std=normal_std_slider.value,
                        uniform_a=new, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)
    uniform_b_slider.start = new

uniform_a_slider.on_change('value', update_uniform_a)

def update_uniform_b(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eval(eps_input.value), p_irm_slider.value,
                        M=int(M_select.value), n=int(n_select.value),
                        irm_type=irm_type_select.value, zipf_a=zipf_a_slider.value, pareto_a=pareto_a_slider.value,
                        pareto_xm=pareto_xm_slider.value, normal_mean=normal_mean_slider.value, normal_std=normal_std_slider.value,
                        uniform_a=uniform_a_slider.value, uniform_b=new)
    mrc_source.data = dict(c=c, hr=hr)
    uniform_a_slider.end = new

uniform_b_slider.on_change('value', update_uniform_b)

layout = row(
    column(M_select, n_select, k_slider, indices_input, eps_input, p),
    column(p_irm_slider, irm_type_select, zipf_a_slider, pareto_a_slider, pareto_xm_slider, normal_mean_slider, normal_std_slider, uniform_a_slider, uniform_b_slider, p2)
)

curdoc().add_root(layout)
