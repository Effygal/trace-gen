
import numpy as np
import trace_gen as tg
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput
from bokeh.plotting import figure

MIN_EPS = 1e-6
MAX_K = 100

def fgen(k, indices, eps=1e-6):
    l = np.full(k, eps)  # Initialize all elements to eps
    s = len(indices)
    l[indices] = (1 - eps) / s  # Assign spike values
    l = l / l.sum()
    return np.arange(len(l)), l 

def mrc_compute(k, indices, eps, p_irm):
    g = tg.TraceGenerator(100, 10000)
    g.set_p_single(0.0)
    x, pdf = fgen(k, indices, eps)
    t, i, _ = g.gen_from_pdf(pdf, p_irm)
    M = len(set(t))
    K = M // 20
    c = np.arange(1, M, K)
    hr_lru = [tg.sim_lru(int(_c), t, raw=True) for _c in c]
    return c, hr_lru

indices = [1,2]
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

def update_k(attrname: str, old: int, new: int):
    print(f'old {attrname}: {old} -> {new}')
    assert isinstance(new, int) and new >= MIN_K
    x,y = fgen(new,eval(indices_input.value), eps_slider.value)
    fgen_source.data = dict(x=x, y=y)
    c, hr = mrc_compute(new, eval(indices_input.value), eps_slider.value, p_irm_slider.value)
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
        k_slider.end = 2*max(new_indices) + 1
    x,y = fgen(k_slider.value,new_indices, eps_slider.value)
    fgen_source.data = dict(x=x, y=y) 
    c, hr = mrc_compute(k_slider.value, new_indices, eps_slider.value, p_irm_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

indices_input.on_change('value', update_indices)

def update_eps(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    assert isinstance(new, float) and new >= 1e-10 and new <= 1/k_slider.value
    x,y = fgen(k_slider.value,eval(indices_input.value), new)
    fgen_source.data = dict(x=x, y=y)
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), new, p_irm_slider.value)
    mrc_source.data = dict(c=c, hr=hr)

eps_slider.on_change('value', update_eps)

def update_p_irm(attrname: str, old: float, new: float):
    print(f'old {attrname}: {old} -> {new}')
    assert isinstance(new, float) and new >= 0.0 and new <= 1.0
    c, hr = mrc_compute(k_slider.value, eval(indices_input.value), eps_slider.value, new)
    mrc_source.data = dict(c=c, hr=hr)

p_irm_slider.on_change('value', update_p_irm)

curdoc().add_root(column(k_slider, indices_input, eps_slider, p_irm_slider, p, p2, width=800))
