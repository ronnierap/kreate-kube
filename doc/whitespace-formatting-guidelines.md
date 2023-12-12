# whitespace formatting guidelines

Sometimes we see diffs with some or many formatting changes.
These can confuse what the diff is really about.

# whitespace
Here are some general rules, to keep it as consistent as possible.
- Only indent using spaces, no tabs (configure your editor(s) to do so on saving)
- Indent yaml code with two spaces, python with four spaces
- Always have no trailing whitespace at the end of line (configure your editor(s) to do so on saving)
- Always end the file with a newline. (configure your editor(s) to do so on saving)
- Always have no extra trailing newline at the end of the file. (configure your editor(s) to do so on saving)

# `git`
In general the most important guidelines is to commit whitespace (and other) formatting changes
in separate git commits from functional changes, bugfixes etc

It is not a problem if you fix whitespace or formatting on some related code that was changed anyway,
but when files are popping up in a git diff / PR that only have formatting changes, this can be confusing.

Also make the comment of the commit clear if it only is formatting changes.
E.g. when reformatting the code with black, make the comment something like `reformatted with black`.

# YAML
when using a list, indent this on the same level as it's parent:
```
# OK
inklude:
- file1
- file2
- file3

# non conforming
inklude:
  - file1
  - file2
  - file3
```
There might be exceptions where the formatting might not be confusing, especially in highly nested lists and maps.
This is a bit of personal taste, and experience with YAML


# Jinja
For jinja some extra rules are needed:

## When a `{{...}}` is embedded in a string without whitespace at at least one side, do not pad it with internal spaces:
```
# OK
file: {{app.appname}}.konf
file: some-prefix-{{app.env}}.postfix

# non conforming
file: {{ app.appname }}.konf
file: some-prefix-{{ app.env }}.postfix

```

## When a `{{...}}` is surrounded by whitespace on both sides, pad it with 1 internal spaces:
```
# OK
name: {{ my.name }}

# non conforming
name: {{my.name}}
```
Most of the jinja code currently follow this convention.
I think it is nice to read, and many other jinja templates I saw follow this convention.
If we want to change this convention to never have whitespace padding, we can change it with a simple sed command.
We should than change this as one big reformatting commit.

## indenting for loops and other blocks
When a for loop, or an if block spans a large block, it is best to put these
statement at the beginning of the line.
You might indent it with 2 spaces if there are multiple nested levels in a large block.

If it is only a small block of 1 or 2 lines, it might look nicer to just keep it
indented at the same level of the template text (often yamk)
