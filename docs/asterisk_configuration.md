# Asterisk Configuration Examples for AI Call Agent

## ari.conf

```ini
[general]
enabled = yes
pretty = yes
websocket_write_timeout = 100

[ai_agent]
type = user
read_only = no
password = ai_agent_secure_password_123
```

## http.conf

```ini
[general]
enabled = yes
bindaddr = 127.0.0.1
bindport = 8088
tlsenable = no
tlsbindaddr = 0.0.0.0:8089
```

## pjsip.conf (Example Trunk Configuration)

```ini
[transport-udp]
type = transport
protocol = udp
bind = 0.0.0.0

[your_trunk]
type = endpoint
context = outbound
disallow = all
allow = alaw,ulaw
aors = your_trunk
auth = your_trunk
outbound_auth = your_trunk

[your_trunk]
type = aor
contact = sip:your_provider_address

[your_trunk]
type = auth
auth_type = userpass
username = your_username
password = your_password

[your_trunk]
type = identify
endpoint = your_trunk
match = your_provider_ip
```

## extensions.conf

```ini
[outbound]
exten => _X.,1,NoOp(Outbound call to ${EXTEN})
same => n,Dial(PJSIP/${EXTEN}@your_trunk,30)
same => n,Hangup()

[default]
exten => s,1,NoOp(Default context)
same => n,Answer()
same => n,Playback(hello-world)
same => n,Hangup()
```

## Installation Steps

1. Edit the configuration files in `/etc/asterisk/`
2. Reload Asterisk configuration:
   ```bash
   asterisk -rx "core reload"
   ```
3. Verify ARI is enabled:
   ```bash
   asterisk -rx "ari show status"
   ```
4. Test ARI connection:
   ```bash
   curl -u ai_agent:ai_agent_secure_password_123 http://127.0.0.1:8088/ari/asterisk/info
   ```
