#/bin/env bash

# Path: .github/actions/shell/cleanup.sh

## ===========================
echo Debugger ...
touch /tmp/keepalive
echo 'created keepalive file.'
echo 'timeout 21000s(5h 50m).'
timeout 21000 bash -c 'stopout=21000; while true;do echo $((stopout=$stopout-3)) > /tmp/stopout ; test -f /tmp/keepalive || break; sleep 3; done ' || echo Timeouted.
echo 'The VM will be shutdown in 10 minutes.'


## ===========================
# Cleanup
curl --location -sSLf --request GET "${jumpserver_host}/api/v1/assets/hosts/" \
  -H "Authorization: Token ${jumpserver_ptoken}" \
  -H 'X-JMS-ORG: 00000000-0000-0000-0000-000000000002' \
  -o hosts.json

echo 'Hosts Info Saved .'

github_hostname="github-$(hostname)"
# shellcheck disable=SC2002
host_id=$(cat hosts.json |jq -r ".[] | select(.name==\"${github_hostname}\") | .id")

echo "host_name: ${github_hostname}"
echo "host_id:   ${host_id}"

curl --location --request DELETE "${jumpserver_host}/api/v1/assets/assets/${host_id}/" \
  -H "Authorization: Token ${jumpserver_ptoken}" \
  -H 'X-JMS-ORG: 00000000-0000-0000-0000-000000000002'


## ===========================
echo "Delete Host from Tailscale: ${github_hostname}."
if command -v tailscale; then
  sudo tailscale down
  sudo tailscale logout
fi
echo down.

echo "shutdown now"