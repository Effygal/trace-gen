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

# tracegen cpp rewrite
executable('trace-gen', tracegen_src, dependencies: [tracegen_deps])

## Import python kernel + numpy core libraries
py_mod = import('python')
py = py_mod.find_installation('python3', pure: true, required: true, modules: ['numpy']) # python_installation object
message('Python path =' + py.full_path() + ', version: ' + py.version())

incdir_pybind11 = run_command(
    py,
    [
        '-c', 'import os; import pybind11; print(os.path.relpath(pybind11.get_include()))',
    ],
    check: true,
).stdout().strip()

_cpp_args = []
_cpp_args += compiler.get_supported_arguments(
    '-O2',
    # '-fsanitize=address',
    # '-fno-omit-frame-pointer',
    # '-g',
    '-Wall',
    '-Wno-sign-compare',
)

## Add directories to include
includes = []
# includes += include_directories('extern')
includes += include_directories(incdir_pybind11)

## Add dependencies
# libdir = meson.current_source_dir() + '/lib'
# deps = []
# foreach dep : ['unroll']
#     deps += compiler.find_library(dep, dirs : libdir)
# endforeach

## Specify source files
python_sources = [
    'src/trace_gen/__init__.py',
    'src/trace_gen/unroll.py',
    'src/trace_gen/misc.py',
    'src/trace_gen/iad_wrapper.py',
    'src/trace_gen/lru_wrapper.py',
    'src/trace_gen/TraceReconstructor.py',
    'src/trace_gen/TraceGenerator.py',
    'src/trace_gen/fifo_wrapper.py',
    'src/trace_gen/clock_wrapper.py',
    #   'src/trace_gen/arc_wrapper.py'
]

## Extension modules
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
    '_fifo',
    sources: ['src/trace_gen/fifo.cpp'],
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
    pure: false # Will be installed next to binaries,
)

# executable('simple', 'simple.cpp', include_directories : includes, dependencies : deps)