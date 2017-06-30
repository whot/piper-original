Piper [![CircleCI](https://circleci.com/gh/libratbag/piper.svg?style=svg&circle-token=7082ad7a7fea706fff66f1547649dca32e446cb0)](https://circleci.com/gh/libratbag/piper)
=====

Piper is a GTK+ application to configure gaming mice, using libratbag via
ratbagd. For the design mockups, see the [Redesign
Wiki](https://github.com/libratbag/piper/wiki/Piper-Redesign).

In order to run Piper, `ratbagd` has to be running (without it, you'll get to
see a pretty mouse trap). To see how, see [its
README](https://github.com/libratbag/libratbag/blob/master/README.md#running-ratbagd-as-dbus-activated-systemd-service).

Installing Piper
================

Piper uses the [meson build system](http://mesonbuild.com/) which in turn uses
[ninja](https://ninja-build.org/) to build and install itself. Run the following
commands to clone Piper and initialize the build:

```
$ git clone https://github.com/libratbag/piper.git
$ cd piper
$ meson builddir --prefix=/usr/
```

To build or re-build after code-changes, run:

```
$ ninja -C builddir
$ sudo ninja -C builddir install
```

Note: `builddir` is the build output directory and can be changed to any other
directory name.

Contributing
============

Yes please. It's best to contact us first to see what you could do. Note that
the devices displayed by Piper come from libratbag.

Piper tries to conform to Python's PEP8 style guide. To verify your code before
opening a PR, please install `flake8` and run the following commands to install
its pre-commit hook:

```
$ flake8 --install-hook git
$ git config --bool flake8.strict true
```

Source
======

`git clone https://github.com/libratbag/piper.git`

Bugs
====

Bugs can be reported in the issue tracker on our GitHub repo:
https://github.com/libratbag/piper/issues

License
=======

Licensed under the GPLv2. See the
[COPYING](https://github.com/libratbag/piper/blob/master/COPYING) file for the
full license information.
