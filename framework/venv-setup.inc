# This is not a standalone script, but should be sourced

if [[ "$VIRTUAL_ENV" == "" ]]; then
  # TODO check if venv is from right directory???
  if [[ ! -d .venv ]]; then
    echo creating venv
    python3 -m venv .venv

    # This is needed because pip version <21.3 does not support pyproject.toml
    echo upgrade to newest version of pip
    python3 -m pip install --upgrade pip
  fi
  if [[ -f .venv/bin/activate ]]; then
    echo activating venv
    . .venv/bin/activate
    if [[ "$VIRTUAL_ENV" != "`pwd`/.venv" ]]; then
      echo WARNING: venv does point to a differen directory $VIRTUAL_ENV
      echo run the following command, and try setup again
      echo "   deactivate"
      CORRECT_VENV=false
      # can not exit, because this is sourced
    fi
  fi
else
  if [[ "$VIRTUAL_ENV" == "`pwd`/.venv" ]]; then
    if [[ -d $VIRTUAL_ENV ]]; then
      echo correct venv already activated
    else
      echo WARNING: venv does not exit at $VIRTUAL_ENV
      echo run the following command, and try setup again
      echo "   deactivate"
      CORRECT_VENV=false
      # can not exit, because this is sourced
    fi
  else
    echo WARNING: WRONG venv activated $VIRTUAL_ENV
    echo run the following command, and try setup again
    echo "   deactivate"
    CORRECT_VENV=false
    # can not exit, because this is sourced
  fi
fi

if $CORRECT_VENV; then
  echo venv setup correctly
fi
