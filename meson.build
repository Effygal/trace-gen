project(
    'trace-gen',
    'cpp',
    default_options: [
        'cpp_std=c++20',
        'buildtype=release',
    ],
)

compiler = meson.get_compiler('cpp')
message('Compiler = ' + compiler.get_id() + ', version: ' + compiler.version())

tracegen_src = [
    'src/trace_gen/tracegen.cc',
]

tracegen_deps = [
    dependency('threads'),
    dependency(
        'boost',
        modules: ['system', 'filesystem', 'program_options', 'thread', 'regex'],
    ),
    dependency('fmt'),
]

executable(
  'trace-gen',
  tracegen_src,
  dependencies: [tracegen_deps],
  install: true,
)

py_mod = import('python')
py = py_mod.find_installation('python3', pure: true, required: false, modules: ['numpy']) # python_installation object
if not py.found()
    py = py_mod.find_installation('/usr/bin/python3', pure: true, required: true, modules: ['numpy'])
endif
message('Python path =' + py.full_path() + ', version: ' + py.version())

incdir_pybind11 = '/usr/include'
pybind11_inc_res = run_command(
    py,
    [
        '-c', 'import os; import pybind11; print(os.path.relpath(pybind11.get_include()))',
    ],
    check: false,
)
if pybind11_inc_res.returncode() == 0
    incdir_pybind11 = pybind11_inc_res.stdout().strip()
else
    message('pybind11 python module not found; using headers from /usr/include')
endif

_cpp_args = []
_cpp_args += compiler.get_supported_arguments(
    '-O2',
    # '-fsanitize=address',
    # '-fno-omit-frame-pointer',
    # '-g',
    '-Wall',
    '-Wno-sign-compare',
    '-stdlib=libstdc++'
)

includes = []
# includes += include_directories('extern')
includes += include_directories(incdir_pybind11)

## Add dependencies
# libdir = meson.current_source_dir() + '/lib'
# deps = []
# foreach dep : ['unroll']
#     deps += compiler.find_library(dep, dirs : libdir)
# endforeach

python_sources = [
    'src/trace_gen/__init__.py',
    'src/trace_gen/unroll.py',
    'src/trace_gen/misc.py',
    'src/trace_gen/iad_wrapper.py',
    'src/trace_gen/lru_wrapper.py',
    'src/trace_gen/lfu_wrapper.py',
    'src/trace_gen/TraceReconstructor.py',
    'src/trace_gen/TraceGenerator.py',
    'src/trace_gen/fifo_wrapper.py',
    'src/trace_gen/fifo_m_wrapper.py',
    'src/trace_gen/clock_wrapper.py',
    'src/trace_gen/ran_clock_wrapper.py',
    'src/trace_gen/ran_sieve_wrapper.py',
    'src/trace_gen/sieve_wrapper.py',
    'src/trace_gen/rand_m_wrapper.py',
    'src/trace_gen/min_wrapper.py',
    #   'src/trace_gen/arc_wrapper.py'
]

module = py.extension_module(
    '_unroll',
    sources: ['src/trace_gen/unroll.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_iad',
    sources: ['src/trace_gen/iad.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_lru',
    sources: ['src/trace_gen/lru.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_lfu',
    sources: ['src/trace_gen/lfu.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_fifo',
    sources: ['src/trace_gen/fifo.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_fifo_m',
    sources: ['src/trace_gen/fifo_m.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_clock',
    sources: ['src/trace_gen/clock.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_ran_clock',
    sources: ['src/trace_gen/ran-clock.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_sieve',
    sources: ['src/trace_gen/sieve.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_ran_sieve',
    sources: ['src/trace_gen/ran-sieve.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_rand_m',
    sources: ['src/trace_gen/rand_m.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

module = py.extension_module(
    '_min',
    sources: ['src/trace_gen/min.cpp'],
    include_directories: includes,
    install: true,
    cpp_args: _cpp_args,
)

# module = py.extension_module(
#   '_arc',
#   sources: ['src/trace_gen/arc.cpp'],
#   include_directories: includes,
#   install: true,
#   cpp_args: _cpp_args
# )

py.install_sources(
    python_sources,
    subdir: 'trace_gen',
    pure: false 
)

# executable('simple', 'simple.cpp', include_directories : includes, dependencies : deps)
