# Using Python for non-python programmers
This document is intended for users that are not familiar with the Python ecosystem.
If you are an experienced Python programmer, you can probably ignore this document
and use your own tools and habits.

`kreate-kube` is written in Python, and thus needs a Python interpreter to run the program.
It is not needed to have any knowledge of the Python programming language, since you can
just write yaml configuration files and run the `kreate-kube` command to process them.

However to install and use different versions of `kreate-kube` you need some understanding
of two basic Python tools:
- `venv`: to have different 'virtual environments' with different versions of tools (like `kreate-kube`)
- `pip`: the "package installer for Python", to easily install and upgrade Python packages
The basic use of these tools is explained below.

## Summary
On a (Linux/MacOs/...) system with bash
```bash
cd project
python3 -m venv .venv        # create a virtual environment named .venv
source .venv/bin/activate    # activate that virtual environment
pip install kreate-kube      # install the newest version in this venv
kreate-kube --help           # run the kreate-kube command
deactivate                   # deactivate your venv when you are done
```

On a Windows machine with PowerShell (or cmd.exe)
```posh
cd project
py -m venv .venv             # create a virtual environment named .venv
.venv\Scripts\activate       # activate that virtual environment
pip install kreate-kube      # install the newest version in this venv
kreate-kube --help           # run the kreate-kube command
deactivate                   # deactivate your venv when you are done
```


## Using Python
On most systems (Linux and Windows) Python is often already installed.
Otherwise there is plenty of documentation online how to install Python.
This text will not go into that, since there are many variations depending
on your situation.

The minimal version required is Python 3.8.
It might be possible to use version 3.7, but this has not been tested.

On Linux/Unix like machines python is usually run from the commandline as follows:
```bash
$ python3                   # start a interactive session

$ python3 <script> ...      # run a python script (usually with extension .py) with some arguments

$ python3 -m <module> ...   # run a module (like venv, pip or kreate.kube) with some arguments
```
Note the `$` is not part of the command, just the shell command prompt

On Windows the commands as above work but usually instead of `python3` you can just use `py`
```posh
PS C:\> py                   # start a interactive session

PS C:\> py <script> ...      # run a python script (usually with extension .py) with some arguments

PS C:\> py -m <module> ...   # run a module (like venv, pip or kreate.kube) with some arguments
```
Note the `PS C:\` is not part of the command, just the command prompt of PowerShell

In the rest of ths text I will use `py` as Python command.

## Using virtual environments with venv
If you would just install a Python package (using `pip`),
it would be installed in some "global" location for your site (computer).
Anywhere you would run Python on your machine, you can use this package.

Although this is convenient, it can easily lead to conflicting versions and other problems.
It might also hamper other Python based tools using specific versions of packages.

In a typical usecase you might have multiple applications using `kreate-kube`.
Some might need the newest version of the tool, while others need an older version,
and might break using the newest version.

This is why you typically install your packages in a virtual environment.
Such a "venv" can easily be created with the Python module `venv` which is
included in Python since version 3.3

### creating a venv
A virtual env can be very easily created in your current directory. with the following command:
```
py -m venv .venv
```
This command will create a directory called `.venv` in your local directory.
Instead of the name `.venv` you can use any other name (like `venv` without the leading period)
and even a different path somewhere else on your machine.
In this document I will assume the directory is called `.venv`
This is quite common and on Linux systems the leading period makes it less visible.
It also is more clear to see the differene the `venv` module and the `.venv` directory

In general you should place the `.venv`  in the directory where your code is,
but it should not be put under version control.
So you should add it to `.gitignore`.

If you ever want to, you can delete the entire `.venv` directory, and start with a clean slate.
In this case you would need to install all the desired packages again.

### activating a venv
Once you created a venv, it is not yet active.
For this you need to activate it.
This can be done easily with the followig command:

On a (Linux/MacOs/...) system with bash
```bash
source .venv/bin/activate    # activate that virtual environment
```

On a Windows machine with PowerShell (or cmd.exe)
```posh
.venv\Scripts\activate       # activate that virtual environment
```

Now you are using a venv with a specific Python version and
with only those packages that you installed in this venv.
Your command prompt will probably be changed to show the venv you are using.

### deactivating a venv
Once you are done working you can deactivate the venv easily using this command:
```
deactivate
```
You prompt and all settings will be changed back to the old situation,
and you will now be using the site/user specific version of python
and installed packages.

Note: It is not needed to deactivate a venv.
You can just exit the shell or command window, or leave this open
in the venv as long as you desire.

## Installing packages with pip
The default way to install packages in Python is by using `pip`.
There are newer tools, for solving specific problems, but in general
pip will be fine for `kreate-kube`, and is generally available.

When creating a venv with `venv` pip is automatically installed in that venv.
You can run it using either
- `py -m pip ...`
- `pip ...`
Outside of a venv, `pip` might not be available, and if it is, you might be careful using
it, because it will install packages site-wide.

Sometimes you will get a deprecation warning by pip, that a newer version is preferred.
You can easily upgrade pip (in your venv) using pip itself:
```
pip install --upgrade pip
```

You can now also install other packages using pip, including `kreate-kube`.
`kreate-kube` is published at PyPI the "Python Package Index", at https://pypi.org/
so it will be found automatically.
If you install the latest version of `kreate-kube` with the following command:
```
pip install kreate-kube
```
All dependencies of kreate-kube will also be installed, as can be seen below.

```posh
(.venv) PS C:\Users\mark\kreate\test> pip install kreate-kube
Collecting kreate-kube
  Obtaining dependency information for kreate-kube from https://files.pythonhosted.org/packages/5b/17/017a1c3ff3adbdd2d2cc265ec3d4c880fed4f6db6298af0be6c59c4f5b11/kreate_kube-0.3.0-py3-none-any.whl.metadata
  Downloading kreate_kube-0.3.0-py3-none-any.whl.metadata (7.9 kB)
Requirement already satisfied: ruamel-yaml>=0.17.32 in c:\users\mark\kreate\test\.venv\lib\site-packages (from kreate-kube) (0.17.32)
Requirement already satisfied: jinja2>=3.1.2 in c:\users\mark\kreate\test\.venv\lib\site-packages (from kreate-kube) (3.1.2)
Requirement already satisfied: cryptography in c:\users\mark\kreate\test\.venv\lib\site-packages (from kreate-kube) (41.0.3)
Requirement already satisfied: MarkupSafe>=2.0 in c:\users\mark\kreate\test\.venv\lib\site-packages (from jinja2>=3.1.2->kreate-kube) (2.1.3)
Requirement already satisfied: ruamel.yaml.clib>=0.2.7 in c:\users\mark\kreate\test\.venv\lib\site-packages (from ruamel-yaml>=0.17.32->kreate-kube) (0.2.7)
Requirement already satisfied: cffi>=1.12 in c:\users\mark\kreate\test\.venv\lib\site-packages (from cryptography->kreate-kube) (1.15.1)
Requirement already satisfied: pycparser in c:\users\mark\kreate\test\.venv\lib\site-packages (from cffi>=1.12->cryptography->kreate-kube) (2.21)
Using cached kreate_kube-0.3.0-py3-none-any.whl (35 kB)
Installing collected packages: kreate-kube
Successfully installed kreate-kube-0.3.0
```


## Advanced scenarios
The setup above describes a
