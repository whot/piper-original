from setuptools import setup

setup(
    name='piper',
    description='Piper is a GUI interface to ratbagd, the system daemon for configurable mice',
    version='0.2',
    url='https://github.com/libratbag/piper',
    license='License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3',
    ],
    keywords='mouse configuration',
    packages=['piper'],
    entry_points={
        'console_scripts': [
            'piper=piper:main',
        ],
    },
    # We require the ratgbagd python bindings but they're currently
    # installed by autotools and that setuptools unable to find the
    # dependencies. Once they're installed by setuptools too we can add
    # the real dependency here, for now you'll need to rely on your
    # packaging system.
    #
    # install_requires=['ratbagd'],
    package_data={'piper': ['piper.ui', '404.svg']},
    zip_safe=False,
    data_files=[('share/applications', ['piper.desktop']),
                ('icons/hicolor/scalable/apps', ['piper.svg'])],
)
