#!/usr/bin/env bash

set -e

# ENV
# authkey: ${{ secrets.AUTHKEY }}
# version:
# args:
# hostname:

VERSION=1.38.4

## ===========================
echo "Check if authkey is set"
# shellcheck disable=SC2154
if [ "$TAILSCALE_AUTH_KEY" == "" ]; then
  echo "TAILSCALE_AUTH_KEY is not set"
  exit 1
fi
echo ok

## ===========================
echo "Check if OS is not Linux"
if [ "${OSTYPE}" != "linux-gnu" ]; then
  echo "OS is not Linux"
  exit 1
fi
echo ok

## ===========================
function change_password() {
  echo "Change Passwd or create user"
  if [ -z "${SHELL_USERNAME}" ]; then
    SHELL_USERNAME="runner"
  fi
  if [ -z "${SHELL_PASSWORD}" ]; then
    echo "SHELL_PASSWORD is not set"
    exit 1
  fi
  if cut -d':' -f1 /etc/passwd | grep -q ${SHELL_USERNAME}; then
    echo "${SHELL_USERNAME}:${SHELL_PASSWORD}" | sudo chpasswd
  else
    sudo useradd -m -s /bin/bash -G sudo -p $(openssl passwd -1 "${SHELL_PASSWORD}") ${SHELL_USERNAME}
  fi
}

## ===========================
function tailscale_install() {
  echo "Download and Install Tailscale"
  MINOR=$(echo "$VERSION" | awk -F '.' '{print $2}')
  if [ $((MINOR % 2)) -eq 0 ]; then
    URL="https://pkgs.tailscale.com/stable/tailscale_${VERSION}_amd64.tgz"
  else
    URL="https://pkgs.tailscale.com/unstable/tailscale_${VERSION}_amd64.tgz"
  fi
  curl "$URL" -o tailscale.tgz
  tar -C /tmp -xzf tailscale.tgz
  rm tailscale.tgz
  TS_PATH=/tmp/tailscale_${VERSION}_amd64
  mkdir -p ~/.local/bin
  mv "${TS_PATH}/tailscale" "${TS_PATH}/tailscaled" ~/.local/bin
  sudo ln -sf ~/.local/bin/tailscale /usr/local/bin/tailscale
  sudo ln -sf ~/.local/bin/tailscaled /usr/local/bin/tailscaled
  sudo mkdir -p /var/lib/tailscale
}

## ===========================
function tailscale_register() {
  echo "Run Tailscale"
  sudo tailscaled 2>~/tailscaled.log &
  if [ -z "${SHELL_HOSTNAME}" ]; then
    SHELL_HOSTNAME="github-$(cat /etc/hostname)"
  fi
  sudo tailscale up --authkey "${TAILSCALE_AUTH_KEY}" --hostname="${SHELL_HOSTNAME}"
}

## ===========================
function check_sshd() {
  echo "Check if sshd is running"
  if ! sudo netstat -ntlp | grep -v grep | grep :22 | grep -q sshd; then
    echo "sshd is not running."
    if [ ! -f /lib/systemd/system/ssh.service ]; then
      echo sshd is not installed. will install ...
      sudo apt-get update
      sudo apt-get install -y openssh-server
    fi
    echo "starting sshd ..."
    sudo systemctl restart sshd
  else
    echo sshd is running.
  fi
}

## ===========================
function jumpserver_register() {
  echo "UPDATE JUMPSERVER..."
  cat >update_data.json <<EOF
{
  "platform": {
      "pk": 1
  },
  "nodes": [
      {
          "pk": "84327184-bd01-4a78-9765-b3748a7ec94d"
      }
  ],
  "protocols": [
      {
          "name": "ssh",
          "port": 22,
          "primary": true,
          "default": false,
          "required": false,
          "secret_types": [
              "password",
              "ssh_key"
          ],
          "setting": {
              "console": false,
              "security": "any",
              "sftp_enabled": true,
              "sftp_home": "/tmp",
              "autofill": "basic",
              "username_selector": "",
              "password_selector": "",
              "submit_selector": "",
              "script": [],
              "auth_username": false
          }
      }
  ],
  "labels": [],
  "is_active": true,
  "name": "__GITHUB_HOSTNAME__",
  "address": "__ADDRESS__",
  "accounts": [
      {
          "name": "__SHELL_USERNAME__",
          "username": "__SHELL_USERNAME__",
          "secret_type": {
              "value": "password",
              "label": "密码"
          },
          "spec_info": {},
          "comment": "",
          "has_secret": true,
          "privileged": true,
          "is_active": true,
          "secret": "__SHELL_PASSWORD__"
      }
  ]
}
EOF

  tailscale_ip=$(tailscale ip | grep -v ':')
  github_hostname="github-$(hostname)"
  if [ -z "$tailscale_ip" ]; then
    echo "tailscale ip is empty."
    exit 1
  fi
  sed -i "s/__GITHUB_HOSTNAME__/${github_hostname}/g" update_data.json
  sed -i "s/__ADDRESS__/${tailscale_ip}/g" update_data.json
  sed -i "s/__SHELL_USERNAME__/${SHELL_USERNAME}/g" update_data.json
  sed -i "s/__SHELL_PASSWORD__/${SHELL_PASSWORD}/g" update_data.json

  echo 'Update Data ----->'
  cat update_data.json
  echo 'Update Data End <-----'

  curl --location --request POST "${JUMPSERVER_HOST}/api/v1/assets/hosts/" \
    -H 'Content-Type: application/json' \
    -H "Authorization: Token ${JUMPSERVER_PTOKEN}" \
    -H 'X-JMS-ORG: 00000000-0000-0000-0000-000000000002' \
    --data-binary @update_data.json

}

function sec2min() {
  tms=$1
  test -n "$tms" || read -r tms
  test -n "$tms" || return 1

  _h=$((tms / 3600)) # 小时数
  _m_s=$((tms - _h * 3600))
  _m=$((_m_s / 60))
  _s=$((tms - _m * 60 - _h * 3600))

  echo "$_h hour $_m minute $_s sec"
}

## ===========================
function jumpserver_unregister() {
  echo Cleanup
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
}

## ===========================
function tailscale_unregister() {
  echo "Delete Host from Tailscale: ${github_hostname}."
  if command -v tailscale; then
    sudo tailscale down
    sudo tailscale logout
  fi
  echo down.

}

echo "shutdown now"

function pre() {
  echo "pre ..."
  change_password
  tailscale_install
  tailscale_register
  check_sshd
  jumpserver_register
  echo 21000 >/tmp/q
  echo "pre done."
  return 0
}

function debugger() {
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

  timeout $stopout bash -c "stopout=21000; while true;do echo $((stopout = stopout - 3)) > /tmp/stopout ; test -f /tmp/keepalive || break; sleep 3; done " || echo Timeouted.
  echo 'The VM will be shutdown in 10 minutes.'
  return 0
}

function post() {
  echo "post ..."
  echo 'remove keepalive file.'
  rm -f /tmp/keepalive
  echo 'remove stopout file.'
  rm -f /tmp/stopout
  echo 'remove jumpserver host.'
  jumpserver_unregister
  echo 'remove tailscale host.'
  tailscale_unregister
  echo 'shutdown now.'
  return 0
}

function main() {
  # 如果不存在stopout file 则认为是 pre
  # 如果存在stopout file，且值大于0 则认为是 debugger
  # 如果存在stopout file，且值为0 则认为是 post
  if [ -f /tmp/stopout ]; then
    stopout=$(cat /tmp/stopout)
    if [ "$stopout" -gt 0 ]; then
      echo "main"
      debugger
      return 0
    else
      echo "post"
      post
      return 0
    fi
  else
    echo "pre"
    pre
    return 0
  fi
}

main
## ===========================
exit 0
