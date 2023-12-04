#!/bin/env bash
curl -sSL https://github.com/fatedier/frp/releases/download/v0.52.3/frp_0.52.3_linux_amd64.tar.gz | tar xzvf -
sudo mv frp_0.52.3_linux_amd64/ /opt/frpc
sudo chown -R runner:runner /opt/frpc

cd /opt/frpc
export HOSTNAME="$(hostname)"

cat > frpc.toml << EOF
serverAddr = "t.leecq.cn"
serverPort = 7000
auth.token = "${FRP_TOKEN}"

[[proxies]]
name = "gh-shell"
type = "tcpmux"
multiplexer = "httpconnect"
subdomain = "$(hostname)"
localIP = "127.0.0.1"
localPort = 22
EOF


cat > frpc.service << EOF
[Unit]
Description = frpc Server
After = network.target syslog.target
Wants = network.target

[Service]
Type = simple
ExecStart = /opt/frpc/frpc -c /opt/frpc/frpc.toml

[Install]
WantedBy = multi-user.target
EOF

sudo cp frpc.service /etc/systemd/system/frpc.service

sudo systemctl start frpc.service
systemctl status frpc.service | cat
