#!/usr/bin/env bash

mkdir -p ~/.local/alist/ ~/.local/bin/
curl -sSLf https://github.com/alist-org/alist/releases/download/v3.15.0/alist-linux-amd64.tar.gz | tar xzvf - -C ~/.local/alist/

mkdir -p ~/.local/alist/data
cat << EOF > ~/.local/alist/data/config.yaml
${{secrets.ALIST_CONFIG}}
EOF
ln -s ~/.local/alist/alist ~/.local/bin/alist
cat << EOF > /usr/lib/systemd/system/alist.service
[Unit]
Description=Alist
After=network.target
Wants=network.target
[Service]
Type=simple
User=runner
Group=runner
WorkingDirectory=/home/runner/.local/alist/
ExecStart=/home/runner/.local/alist/alist --data /home/runner/.local/alist/data/config.yaml
Restart=on-failure
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable alist
systemctl start alist