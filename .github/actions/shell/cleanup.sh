#!/usr/bin/env bash

# Path: .github/actions/shell/cleanup.sh
function sec2min() {
    tms=$1
    test -n "$tms" || read -r tms
    test -n "$tms" || return 1

    _h=$((tms / 3600))  # 小时数
    _m_s=$((tms - _h * 3600))
    _m=$((_m_s / 60 ))
    _s=$((tms - _m * 60 - _h * 3600 ))

    echo "$_h hour $_m minute $_s sec"
}

## ===========================
echo Debugger ...
touch /tmp/keepalive
echo 'created keepalive file.'
if [ -f /tmp/stopout ]; then
  echo 'stopout file exists.'
  stopout=$(cat /tmp/stopout)
else
  echo 'stopout file not exists.'
  stopout=21000
fi

export stopout
echo "timeout ${stopout}($(sec2min ${stopout}))."

timeout $stopout bash -c "stopout=21000; while true;do echo $((stopout=stopout-3)) > /tmp/stopout ; test -f /tmp/keepalive || break; sleep 3; done " || echo Timeouted.
echo 'The VM will be shutdown in 10 minutes.'


## ===========================
# Cleanup
curl --location -sSLf --request GET "${JUMPSERVER_HOST}/api/v1/assets/hosts/" \
  -H "Authorization: Token ${JUMPSERVER_PTOKEN}" \
  -H 'X-JMS-ORG: 00000000-0000-0000-0000-000000000002' \
  -o hosts.json

echo 'Hosts Info Saved .'

github_hostname=${SHELL_HOSTNAME}
if [ "${github_hostname}" == "" ]; then
  github_hostname="github-$(hostname)"
fi

host_id=$(jq -r ".[] < hosts.json | select(.name==\"${github_hostname}\") | .id")

echo "host_name: ${github_hostname}"
echo "host_id:   ${host_id}"

curl --location --request DELETE "${JUMPSERVER_HOST}/api/v1/assets/assets/${host_id}/" \
  -H "Authorization: Token ${JUMPSERVER_PTOKEN}" \
  -H 'X-JMS-ORG: 00000000-0000-0000-0000-000000000002'

echo 'removed host from jumpserver.'


## ===========================
echo "Delete Host from Tailscale: ${github_hostname}."
if command -v tailscale; then
  sudo tailscale down
  sudo tailscale logout
fi
echo down.

echo "shutdown now"