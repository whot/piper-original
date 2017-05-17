project('piper',
	version: '0.2.1',
	license: 'GPLv2',
	meson_version: '>= 0.40.0')

# Dependencies
dependency('python3', required: true)
dependency('pygobject-3.0', required: true)

prefix = get_option('prefix')
datadir = join_paths(prefix, get_option('datadir'))
localedir = join_paths(prefix, get_option('localedir'))
pkgdatadir = join_paths(datadir, meson.project_name())

subdir('data')

# Find the directory to install our Python code
python = import('python3')
py3 = python.find_python()
message('Getting Python3 install dir')
python_dir = python.sysconfig_path('purelib')
if not python_dir.endswith('site-packages')
	error('Python3 purelib path seems invalid')
endif
install_subdir('piper', install_dir: python_dir)

conf = configuration_data()
conf.set('pkgdatadir', pkgdatadir)
conf.set('localedir', localedir)

configure_file(input: 'piper.in',
	       output: 'piper',
	       configuration: conf,
	       install_dir: 'bin')

meson.add_install_script('meson_install.sh')
