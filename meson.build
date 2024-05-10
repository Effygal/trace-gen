project('trace-gen', 'cpp')

compiler = meson.get_compiler('cpp')
message('Compiler = '+compiler.get_id()+', version: '+compiler.version())

## Import python kernel + numpy core libraries
py_mod = import('python')
py = py_mod.find_installation(pure: true, required: true, modules: ['numpy']) # python_installation object
message('Python path =' + py.full_path() + ', version: ' + py.version())

incdir_pybind11 = run_command(py, ['-c', 'import os; os.chdir(".."); import pybind11; print(pybind11.get_include())'], check : true).stdout().strip()

_cpp_args = []
_cpp_args += compiler.get_supported_arguments(
  '-O2',
  # '-fsanitize=address', 
  # '-fno-omit-frame-pointer',
  # '-g',
  '-Wall',
  '-Wno-sign-compare'
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
  'src/trace_gen/clock_wrapper.py'
]

## Extension modules
module = py.extension_module(
  '_unroll',      
  sources: ['src/trace_gen/unroll.cpp'],
  include_directories: includes,
  install: true,
  cpp_args: _cpp_args
)

module = py.extension_module(
  '_iad',      
  sources: ['src/trace_gen/iad.cpp'],
  include_directories: includes,
  install: true,
  cpp_args: _cpp_args
)

module = py.extension_module(
  '_lru',      
  sources: ['src/trace_gen/lru.cpp'],
  include_directories: includes,
  install: true,
  cpp_args: _cpp_args
)

module = py.extension_module(
  '_fifo',      
  sources: ['src/trace_gen/fifo.cpp'],
  include_directories: includes,
  install: true,
  cpp_args: _cpp_args
)

module = py.extension_module(
  '_clock',      
  sources: ['src/trace_gen/clock.cpp'],
  include_directories: includes,
  install: true,
  cpp_args: _cpp_args
)

py.install_sources(
  python_sources,
  subdir: 'trace_gen', 
  pure: false       # Will be installed next to binaries
)

# executable('simple', 'simple.cpp', include_directories : includes, dependencies : deps)
