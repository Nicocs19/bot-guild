#!/bin/bash
# Instala Hogger en un servidor Linux (Google Cloud e2-micro, Debian/Ubuntu) para que ande 24/7.
# Uso: subí Hogger_bot.zip al servidor y corré:  bash instalar_servidor.sh   (o: unzip Hogger_bot.zip && bash bot/instalar_servidor.sh)
set -e
cd ~
if [ -f Hogger_bot.zip ]; then unzip -oq Hogger_bot.zip; fi
cd ~/bot
echo "=== Instalando lo necesario (tarda 1 o 2 minutos) ==="
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip unzip >/dev/null
# memoria extra (swap) para que no le falte RAM a la máquina chiquita
if [ ! -f /swapfile ]; then sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile >/dev/null && sudo swapon /swapfile && echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null; fi
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
if [ ! -f .env ]; then
  echo
  read -rsp "Pegá el TOKEN del bot (no se ve mientras pegás) y Enter: " T; echo
  read -rp  "Pegá el ID del server y Enter: " G
  printf "DISCORD_TOKEN=%s\nGUILD_ID=%s\n" "$T" "$G" > .env
  chmod 600 .env
fi
sudo tee /etc/systemd/system/hogger.service >/dev/null <<EOF
[Unit]
Description=Hogger, bot de The H's
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$HOME/bot
ExecStart=$HOME/bot/.venv/bin/python bot.py
Restart=always
RestartSec=10
Environment=PYTHONIOENCODING=utf-8

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now hogger
sleep 8
echo
sudo systemctl --no-pager --lines=5 status hogger || true
echo
echo "=== Listo. Hogger queda prendido 24/7 y arranca solo si el servidor se reinicia. ==="
echo "Ver qué hace:   sudo journalctl -u hogger -f      (Ctrl+C para salir)"
echo "Reiniciarlo:    sudo systemctl restart hogger"
