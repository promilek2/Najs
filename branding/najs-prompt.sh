# shellcheck shell=bash
if [[ $- == *i* ]] && [[ -z ${NAJS_NO_PROMPT:-} ]] && [[ ${TERM:-dumb} != dumb ]]; then
  NAJS_PROMPT_GENERATION=unknown
  if [[ -r /etc/najs-release ]]; then
    while IFS='=' read -r key value; do
      if [[ ${key} == NAJS_GENERATION ]]; then
        NAJS_PROMPT_GENERATION=${value//\"/}
        break
      fi
    done </etc/najs-release
  fi

  _najs_prompt_command() {
    local status=$?
    local status_color='\[\e[38;2;89;210;255m\]'
    if (( status != 0 )); then
      status_color='\[\e[38;2;255;102;122m\]'
    fi
    PS1="${status_color}najs:${NAJS_PROMPT_GENERATION}\[\e[0m\] \[\e[38;2;169;192;207m\]\w\[\e[0m\]\n\\$ "
  }

  PROMPT_COMMAND=_najs_prompt_command
fi
