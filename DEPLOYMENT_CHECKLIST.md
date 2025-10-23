# Deployment Checklist

Use this checklist when deploying the AI Call Agent system.

## Pre-Deployment

- [ ] Ubuntu 22.04 LTS server prepared
- [ ] Asterisk 20.15.2 installed and running
- [ ] MySQL/MariaDB installed and running
- [ ] Python 3.8+ installed
- [ ] SIP trunk configured for outbound calls
- [ ] OpenAI API key obtained
- [ ] Sufficient disk space (minimum 50GB)
- [ ] Minimum 8GB RAM available

## Installation

- [ ] Repository cloned: `git clone https://github.com/berndmarcel860-byte/Agcai.git`
- [ ] Entered directory: `cd Agcai`
- [ ] Made setup script executable: `chmod +x setup.sh`
- [ ] Ran setup script: `./setup.sh`
- [ ] Virtual environment created successfully

## Configuration

- [ ] Copied `.env.example` to `.env`
- [ ] Set MySQL credentials in `.env`:
  - [ ] DB_HOST=127.0.0.1
  - [ ] DB_PORT=3306
  - [ ] DB_USER=aiagent
  - [ ] DB_PASS=AiAgent990 (change in production!)
  - [ ] DB_NAME=ai_calls
- [ ] Set ARI credentials in `.env`:
  - [ ] ARI_HOST=127.0.0.1
  - [ ] ARI_PORT=8088
  - [ ] ARI_USER=ai_agent
  - [ ] ARI_PASS=ai_agent_secure_password_123 (change in production!)
  - [ ] ARI_APP=aiagent
- [ ] Set OpenAI API key: OPENAI_API_KEY=sk-...
- [ ] Set outbound caller ID: OUTBOUND_CALLER_ID=+49...
- [ ] Review and adjust other settings as needed

## MySQL Database Setup

- [ ] MySQL server running: `sudo systemctl status mysql`
- [ ] Created database: `CREATE DATABASE ai_calls;`
- [ ] Created user: `CREATE USER 'aiagent'@'localhost' IDENTIFIED BY 'AiAgent990';`
- [ ] Granted privileges: `GRANT ALL PRIVILEGES ON ai_calls.* TO 'aiagent'@'localhost';`
- [ ] Flushed privileges: `FLUSH PRIVILEGES;`
- [ ] Tested connection: `mysql -u aiagent -p ai_calls`

## Asterisk Configuration

- [ ] Edited `/etc/asterisk/ari.conf`:
  - [ ] Enabled ARI: `enabled = yes`
  - [ ] Created user `ai_agent` with password
- [ ] Edited `/etc/asterisk/http.conf`:
  - [ ] Enabled HTTP: `enabled = yes`
  - [ ] Set bind address and port
- [ ] Configured SIP trunk in `/etc/asterisk/pjsip.conf`
- [ ] Configured dialplan in `/etc/asterisk/extensions.conf`
- [ ] Reloaded Asterisk: `asterisk -rx "core reload"`
- [ ] Verified ARI status: `asterisk -rx "ari show status"`
- [ ] Tested ARI connection: `curl -u ai_agent:password http://127.0.0.1:8088/ari/asterisk/info`

## Database Initialization

- [ ] Activated virtual environment: `source venv/bin/activate`
- [ ] Initialized database schema: `python main.py --init-db`
- [ ] Verified tables created: `mysql -u aiagent -p ai_calls -e "SHOW TABLES;"`
- [ ] Checked for errors in logs

## Test Run

- [ ] Prepared test leads in CSV file
- [ ] Started test campaign: `python main.py --campaign "Test" --leads test_leads.csv`
- [ ] Monitored logs: `tail -f logs/aiagent.log`
- [ ] Verified call initiation in Asterisk: `asterisk -rx "core show channels"`
- [ ] Checked database for call records
- [ ] Reviewed conversation logs
- [ ] Stopped campaign with Ctrl+C

## Security Hardening (Production)

- [ ] Changed all default passwords
- [ ] Generated strong MySQL password
- [ ] Generated strong ARI password
- [ ] Restricted ARI to localhost only
- [ ] Configured firewall rules
- [ ] Enabled MySQL SSL (if remote)
- [ ] Set up fail2ban for SSH
- [ ] Reviewed and minimized user permissions
- [ ] Disabled root MySQL login
- [ ] Configured log rotation
- [ ] Set up automated backups

## Production Deployment

- [ ] Created systemd service file: `/etc/systemd/system/aiagent.service`
- [ ] Enabled service: `sudo systemctl enable aiagent`
- [ ] Started service: `sudo systemctl start aiagent`
- [ ] Verified service status: `sudo systemctl status aiagent`
- [ ] Checked service logs: `sudo journalctl -u aiagent -f`
- [ ] Configured log monitoring
- [ ] Set up alerts for failures
- [ ] Scheduled database backups

## Monitoring Setup

- [ ] Log directory accessible: `logs/`
- [ ] Log rotation configured
- [ ] Monitoring script created (optional)
- [ ] Alerts configured for errors
- [ ] Database backup script created
- [ ] Backup cron job scheduled
- [ ] Resource monitoring enabled (CPU, RAM, disk)

## Performance Testing

- [ ] Tested with 1 concurrent call
- [ ] Tested with max concurrent calls
- [ ] Monitored CPU usage under load
- [ ] Monitored memory usage under load
- [ ] Tested database performance
- [ ] Verified TTS/STT model loading
- [ ] Checked audio quality
- [ ] Measured average call duration

## Documentation Review

- [ ] Read README.md completely
- [ ] Reviewed QUICKSTART.md
- [ ] Checked API documentation
- [ ] Reviewed Asterisk configuration examples
- [ ] Studied usage examples
- [ ] Understood deployment guide

## Final Checks

- [ ] All services running: MySQL, Asterisk, AI Agent
- [ ] No errors in logs
- [ ] Database accessible
- [ ] ARI connection working
- [ ] OpenAI API responding
- [ ] Audio models loaded
- [ ] Test calls successful
- [ ] Appointments being created
- [ ] Data persisting correctly

## Post-Deployment

- [ ] Monitor first production campaign
- [ ] Review call quality
- [ ] Check appointment accuracy
- [ ] Analyze conversation logs
- [ ] Gather feedback
- [ ] Tune AI prompts if needed
- [ ] Adjust concurrent call limit
- [ ] Optimize database queries
- [ ] Document any customizations

## Maintenance Schedule

- [ ] Daily: Check logs for errors
- [ ] Weekly: Review campaign statistics
- [ ] Weekly: Check disk space
- [ ] Monthly: Update dependencies
- [ ] Monthly: Optimize database
- [ ] Quarterly: Security audit
- [ ] Quarterly: Backup testing

## Troubleshooting Resources

- [ ] Logs location: `logs/aiagent.log`
- [ ] Asterisk logs: `/var/log/asterisk/`
- [ ] MySQL logs: `/var/log/mysql/`
- [ ] System logs: `journalctl -u aiagent`
- [ ] Check README.md troubleshooting section
- [ ] Review GitHub issues
- [ ] Contact support if needed

## Success Criteria

- [x] System starts without errors
- [x] Calls are initiated successfully
- [x] AI conversations work properly
- [x] Speech recognition accurate
- [x] Speech synthesis clear
- [x] Appointments scheduled correctly
- [x] Data saved to database
- [x] No security vulnerabilities
- [x] Performance acceptable
- [x] Logs show expected behavior

---

## Notes

Add any deployment-specific notes here:

- Network configuration details
- Custom Asterisk settings
- Specific lead sources
- Integration requirements
- Team contacts
- Escalation procedures

---

**Deployment Date:** _____________

**Deployed By:** _____________

**Environment:** ☐ Development  ☐ Staging  ☐ Production

**Sign-off:** _____________
