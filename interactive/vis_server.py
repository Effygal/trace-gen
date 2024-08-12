import numpy as np
import trace_gen as tg
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput, Select
from bokeh.plotting import figure

MIN_EPS = 1e-6
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

def mrc_compute(k, indices, eps, p_irm, irm_type=None, zipf_a=None, pareto_a=None, pareto_xm=None, normal_mean=None, normal_std=None, uniform_a=None, uniform_b=None):
    g = tg.TraceGenerator(100, 10000)
    if irm_type is not None:
        gset(g, irm_type, zipf_a, pareto_a, pareto_xm, normal_mean, normal_std, uniform_a, uniform_b)
    x, pdf = fgen(k, indices, eps)
    t, i, _ = g.gen_from_pdf(pdf, p_irm)
    M = len(set(t))
    K = M // 20
    c = np.arange(1, M, K)
    hr_lru = [tg.sim_lru(int(_c), t, raw=True) for _c in c]
    return c, hr_lru

indices = [1, 2]
eps = 5e-3 
MIN_K = max(indices) + 1
x, y = fgen(MIN_K, indices, eps)
P_IRM_MIN = 0.0
p_irm = P_IRM_MIN
c, hr = mrc_compute(MIN_K, indices, eps, p_irm)

fgen_source = ColumnDataSource(data=dict(x=x, y=y))
mrc_source = ColumnDataSource(data=dict(c=c, hr=hr))

p = figure(title="f", width=350, height=350)
p.line(x='x', y='y', line_width=2, source=fgen_source)

p2 = figure(title="MRC", width=350, height=350)
p2.line(x='c', y='hr', line_width=2, source=mrc_source)

k_slider = Slider(
    start=MIN_K, end=MAX_K, value=MIN_K, step=1, title="k parameter"
)
indices_input = TextInput(
    value=str(indices), title="Spike indices"
)
eps_slider = Slider(
    title="Epsilon", value=eps, start=MIN_EPS, end=1/k_slider.value, step=1e-3
)

p_irm_slider = Slider(
    title="p_irm", value=p_irm, start=0.0, end=1.0, step=0.01
)

# Adding widgets for gset function parameters
irm_type_select = Select(title="IRM Type", value="zipf", options=["zipf", "pareto", "normal", "uniform"])
zipf_a_slider = Slider(title="Zipf a", value=1.2, start=1.0, end=10.0, step=0.1)
pareto_a_slider = Slider(title="Pareto a", value=2.5, start=1.0, end=10.0, step=0.1)
pareto_xm_slider = Slider(title="Pareto xm", value=0.0, start=0.0, end=100.0, step=0.1)
normal_mean_slider = Slider(title="Normal Mean", value=50.0, start=0.0, end=100.0, step=1)
normal_std_slider = Slider(title="Normal Std", value=16, start=0, end=100, step=1)
uniform_a_slider = Slider(title="Uniform a", value=0.0, start=0.0, end=100, step=1)
uniform_b_slider = Slider(title="Uniform b", value=100, start=0, end=100, step=1)

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
    assert isinstance(new, int) and new >= MIN_K
    x, y = fgen(new, eval(indices_input.value), eps_slider.value)
    fgen_source.data = dict(x=x, y=y)
    c, hr = mrc_compute(new, eval(indices_input.value), eps_slider.value, p_irm_slider.value,
                        irm_type_select.value, zipf_a_slider.value, pareto_a_slider.value,
                        pareto_xm_slider.value, normal_mean_slider.value, normal_std_slider.value,
                        uniform_a_slider.value, uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)
    eps_slider.end = 1/new

k_slider.on_change('value', update_k)

def update_indices(attrname: str, old: str, new: str):
    print(f'old {attrname}: {old} -> {new}')
    new_indices = eval(new)
    assert isinstance(new_indices, list)
    if max(new_indices) >= k_slider.value:
        k_slider.start = max(new_indices) + 1
        k_slider.value = max(new_indices) + 1
        k_slider.end = 2 * max(new_indices) + 1
    x, y = fgen(k_slider.value, new_indices, eps_slider.value)
    fgen_source.data = dict(x=x, y=y)
    c, hr = mrc_compute(k_slider.value, new_indices, eps_slider.value, p_irm_slider.value,
                        irm_type_select.value, zipf_a_slider.value, pareto_a_slider.value,
                        pareto_xm_slider.value, normal_mean_slider.value, normal_std_slider.value,
                        uniform_a_slider.value, uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

indices_input.on_change('value', update_indices)

def update_eps(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    assert isinstance(new, float) and new >= 1e-10 and new <= 1/k_slider.value
    x, y = fgen(k_slider.value, eval(indices_input.value), new)
    fgen_source.data = dict(x=x, y=y)
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), new, p_irm_slider.value,
                        irm_type_select.value, zipf_a_slider.value, pareto_a_slider.value,
                        pareto_xm_slider.value, normal_mean_slider.value, normal_std_slider.value,
                        uniform_a_slider.value, uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

eps_slider.on_change('value', update_eps)

def update_p_irm(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    assert isinstance(new, float) and new >= 0.0 and new <= 1.0
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eps_slider.value, new,
                        irm_type_select.value, zipf_a_slider.value, pareto_a_slider.value,
                        pareto_xm_slider.value, normal_mean_slider.value, normal_std_slider.value,
                        uniform_a_slider.value, uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

p_irm_slider.on_change('value', update_p_irm)

# Update functions for gset parameters
def update_irm_type(attrname, old, new):
    print(f'old {attrname}: {old} -> {new}')
    
    # Hide all parameter sliders
    zipf_a_slider.visible = False
    pareto_a_slider.visible = False
    pareto_xm_slider.visible = False
    normal_mean_slider.visible = False
    normal_std_slider.visible = False
    uniform_a_slider.visible = False
    uniform_b_slider.visible = False

    # Show only the relevant sliders
    if new == "zipf":
        zipf_a_slider.visible = True
    elif new == "pareto":
        pareto_a_slider.visible = True
        pareto_xm_slider.visible = True
    elif new == "normal":
        normal_mean_slider.visible = True
        normal_std_slider.visible = True
    elif new == "uniform":
        uniform_a_slider.visible = True
        uniform_b_slider.visible = True

    # Recompute the MRC with the new IRM type
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eps_slider.value, p_irm_slider.value,
                        new, zipf_a_slider.value, pareto_a_slider.value,
                        pareto_xm_slider.value, normal_mean_slider.value, normal_std_slider.value,
                        uniform_a_slider.value, uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

irm_type_select.on_change('value', update_irm_type)

def update_zipf_a(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eps_slider.value, p_irm_slider.value,
                        irm_type_select.value, new)
    mrc_source.data = dict(c=c, hr=hr)

zipf_a_slider.on_change('value', update_zipf_a)

def update_pareto_a(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eps_slider.value, p_irm_slider.value,
                        irm_type_select.value, pareto_a=new, pareto_xm=pareto_xm_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

pareto_a_slider.on_change('value', update_pareto_a)

def update_pareto_xm(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eps_slider.value, p_irm_slider.value,
                        irm_type_select.value, pareto_a=pareto_a_slider.value, pareto_xm=new)
    mrc_source.data = dict(c=c, hr=hr)

pareto_xm_slider.on_change('value', update_pareto_xm)

def update_normal_mean(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eps_slider.value, p_irm_slider.value,
                        irm_type_select.value, normal_mean=new, normal_std=normal_std_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

normal_mean_slider.on_change('value', update_normal_mean)

def update_normal_std(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eps_slider.value, p_irm_slider.value,
                        irm_type_select.value, normal_mean=normal_mean_slider.value, normal_std=new)
    mrc_source.data = dict(c=c, hr=hr)

normal_std_slider.on_change('value', update_normal_std)

def update_uniform_a(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eps_slider.value, p_irm_slider.value,
                        irm_type_select.value, uniform_a=new, uniform_b=uniform_b_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

uniform_a_slider.on_change('value', update_uniform_a)

def update_uniform_b(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eps_slider.value, p_irm_slider.value,
                        irm_type_select.value, uniform_a=uniform_a_slider.value, uniform_b=new)
    mrc_source.data = dict(c=c, hr=hr)

uniform_b_slider.on_change('value', update_uniform_b)

layout = row(
    column(k_slider, indices_input, eps_slider, p_irm_slider,),
    column(irm_type_select, zipf_a_slider, pareto_a_slider, pareto_xm_slider, normal_mean_slider, normal_std_slider, uniform_a_slider, uniform_b_slider),
    column(p, p2)
)

curdoc().add_root(layout)
