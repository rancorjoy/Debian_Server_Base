#!/bin/bash
set -euo pipefail

# Store a log file in /var/log/late_command.log to allow debugging inside the new OS
exec > /var/log/late_command.log 2>&1

# Tell user this script is running in the command terminal output of the Debian installer (before system reboot)
echo "=== Starting late_command finish script ==="
date

# Variables that will be passed by the preseed generator (from .env)
USER_NAME="$USER_NAME$"
SSH_PORT="$SSH_PORT$"
NET_IFACE="$NET_IFACE$"
STATIC_IP="$STATIC_IP$"
NETMASK="$NETMASK$"
GATEWAY="$GATEWAY$"
DNS_SERVERS="$DNS_SERVERS$"



# 1. SSH key setup (line-separated keys)

# Create SSH Location in Debian with proper permissions
echo "[*] Configuring SSH authorized_keys"
mkdir -p /home/${USER_NAME}/.ssh
chmod 700 /home/${USER_NAME}/.ssh

# If the Authorized Key File is found in the ISO, copy it; If not, warn the user (in the late command log)
if [[ -f /tmp/authorized_keys ]]; then
    echo "[+] Found /tmp/authorized_keys - copying"
    cp /tmp/authorized_keys /home/${USER_NAME}/.ssh/authorized_keys
else
    echo "[!] WARNING: /tmp/authorized_keys not found"
    touch /home/${USER_NAME}/.ssh/authorized_keys
fi

# Create Authorized Key File in Debian with proper permissions
chmod 600 /home/${USER_NAME}/.ssh/authorized_keys
chown -R ${USER_NAME}:${USER_NAME} /home/${USER_NAME}/.ssh

# Print authorized public keys to terminal screen as comfirmation that keys were installed
echo "[*] Final authorized_keys content:"
cat /home/${USER_NAME}/.ssh/authorized_keys || true


# 2. SSH hardening via drop-in (modern method)

# Tell user that SSH hardening has begun and create file location for SSH config
echo "[*] Writing sshd drop-in config"
mkdir -p /etc/ssh/sshd_config.d

# Add the following settings to the SSH configuration file (until EOF)
cat > /etc/ssh/sshd_config.d/99-hardening.conf <<EOF
Port ${SSH_PORT}
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
AllowTcpForwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

# Make sure the main config includes the drop-in directory
# (Debian does this by default, done explicitly for safety)
grep -q '^Include /etc/ssh/sshd_config.d/\*.conf' /etc/ssh/sshd_config \
    echo 'Include /etc/ssh/sshd_config.d/*.conf' >> /etc/ssh/sshd_config



# 3. UFW Configuration

# Alert user that UFW configuration is beginning
echo "[*] Preparing first-boot UFW script"

# Add the following settings to the UFW configuration file (until EOF)
cat > /etc/rc.local <<EOF
#!/bin/sh
ufw default deny incoming
ufw default allow outgoing
ufw allow ${SSH_PORT}/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
rm -f /etc/rc.local
EOF

# Make UFW configuration run last before reboot
chmod +x /etc/rc.local
sed -i 's/ENABLED=no/ENABLED=yes/' /etc/ufw/ufw.conf



# 4. Fail2Ban

echo "[*] Configuring Fail2Ban"

cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
backend = systemd

[sshd]
enabled = true
port = ${SSH_PORT}
EOF


# 5. Hardware blacklists (prevent wireless IoT functionality)

echo "[*] Blacklisting wireless modules"

cat > /etc/modprobe.d/blacklist-wireless.conf <<EOF
blacklist b43
blacklist bcma
blacklist iwlwifi
blacklist ath9k
blacklist ath10k_pci
blacklist rtw88
blacklist mt76
blacklist bluetooth
EOF

update-initramfs -u



# 6. Static network configuration

echo "[*] Writing static network config"

cat > /etc/network/interfaces <<EOF
auto lo
iface lo inet loopback

auto ${NET_IFACE}
iface ${NET_IFACE} inet static
    address ${STATIC_IP}
    netmask ${NETMASK}
    gateway ${GATEWAY}
    dns-nameservers ${DNS_SERVERS}
EOF



# 7. Enable services

echo "[*] Enabling services"

systemctl enable unattended-upgrades
systemctl enable fail2ban
systemctl enable ssh

echo "=== finish script completed successfully ==="
date