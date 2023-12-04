# History of kreate-kube
This is a rewrite of a similar project written as bash scripts.
The bash scripts have been used for deploying over 30 applications to
development, acceptance and production environments.

However the bash scripting language was not the best choice, so Python was chosen
for several reasons:
- Large bash scripts are difficult to maintain
  - google coding guidelines demand that bash scripts over 100 lines long are to be rewritten in Python.
    See https://google.github.io/styleguide/shellguide.html#when-to-use-shell, which states:
    > if you are writing a script that is more than 100 lines long, or that uses non-straightforward control flow logic,
    > you should rewrite it in a more structured language now.
    > Bear in mind that scripts grow.
    > Rewrite your script early to avoid a more time-consuming rewrite at a later date.
  - not many devops team members are proficient in bash
  - no OO and limited var scoping (most vars are global vars)
- Possibility to run natively on Windows (with Python installed)
  - no CRLF problems
  - Windows can recognizes `*.py` extension to prevent Linux file permission problems on Windows filesystems
- Much cleaner code
  - yaml parser
  - jinja templates
  - modular design, where a team can add team-specific templates and defaults for their set of applications
  - powerful requirements.txt/pip dependency management

Initially the idea was to use python scripts just like we were doing in bash.
The yaml konfiguration became so powerful, that scripting was not needed
at all, and you could specify everything in yaml (and jinja2 templates).

The new approach is to use only yaml and jinja2, even for extending the
framework with new templates and other behaviour.
