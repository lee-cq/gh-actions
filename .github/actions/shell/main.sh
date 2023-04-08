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
echo "Change Passwd or create user"
if [ -z "${SHELL_USERNAME}" ]; then
  SHELL_USERNAME="runner"
fi
if [ -z "${SHELL_PASSWORD}" ]; then
    echo "SHELL_PASSWORD is not set"
    exit 1
fi
if cut -d':' -f1 /etc/passwd | grep -q ${SHELL_USERNAME} ;then
  echo "${SHELL_USERNAME}:${SHELL_PASSWORD}" | sudo chpasswd
else
  sudo useradd -m -s /bin/bash -G sudo -p $(openssl passwd -1 "${SHELL_PASSWORD}") ${SHELL_USERNAME};
fi

## ===========================
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

## ===========================
echo  "Run Tailscale"
sudo tailscaled 2>~/tailscaled.log &
if [ -z "${SHELL_HOSTNAME}" ]; then
  SHELL_HOSTNAME="github-$(cat /etc/hostname)"
fi
sudo tailscale up --authkey "${authkey}" --hostname="${SHELL_HOSTNAME}"

## ===========================
echo "Check if sshd is running"
if ! sudo netstat -ntlp |grep -v grep |grep :22 | grep -q sshd ; then
  echo "sshd is not running."
  if [ ! -f /lib/systemd/system/ssh.service ]; then
    echo sshd is not installed. will install ...
    sudo apt-get update;
    sudo apt-get install -y openssh-server;
  fi
  echo "starting sshd ..."
  sudo systemctl restart sshd
else
  echo sshd is running.
fi
## ===========================
echo "UPDATE JUMPSERVER..."
cat > update_data.json << EOF
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

tailscale_ip=$(tailscale ip |grep -v ':')
github_hostname="github-$(hostname)"
if [ -z "$tailscale_ip" ]; then
    echo "tailscale ip is empty."
    exit 1
fi
sed -i "s/__GITHUB_HOSTNAME__/${github_hostname}/g" update_data.json
sed -i "s/__ADDRESS__/${tailscale_ip}/g" update_data.json
sed -i "s/__SHELL_USERNAME__/${SHELL_USERNAME}/g" update_data.json
sed -i "s/__SHELL_PASSWORD__/${SHELL_PASSWORD}/g" update_data.json

echo 'Update Data ----->';
cat update_data.json
echo 'Update Data End <-----';

curl --location --request POST "${JUMPSERVER_HOST}/api/v1/assets/hosts/" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Token ${JUMPSERVER_PTOKEN}" \
  -H 'X-JMS-ORG: 00000000-0000-0000-0000-000000000002' \
  --data-binary @update_data.json
