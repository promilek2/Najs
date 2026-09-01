# shellcheck shell=sh
case $- in
  *i*)
    if [ -t 1 ] && [ -z "${NAJS_NO_FASTFETCH:-}" ] \
      && [ -z "${NAJS_FASTFETCH_SHOWN:-}" ] && command -v fastfetch >/dev/null 2>&1; then
      export NAJS_FASTFETCH_SHOWN=1
      fastfetch --config /etc/xdg/fastfetch/config.jsonc
    fi
    ;;
esac
