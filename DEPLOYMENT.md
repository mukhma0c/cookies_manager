# Cookie Manager Deployment Guide

This guide provides instructions for deploying the Cookie Manager application in a production environment using Nginx, Gunicorn, and systemd.

## System Requirements

- Ubuntu 22.04 LTS or similar Linux distribution
- Python 3.12+
- Nginx
- SQLite 3
- Git

## Installation Steps

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv sqlite3 nginx git
```

### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/cookiemgr.git
cd cookiemgr
```

### 3. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 4. Initialize the Database

```bash
export FLASK_APP=app.py
export FLASK_CONFIG=production
flask db upgrade
python seed.py  # Optional if you want sample data
```

### 5. Configure Environment

Create a `.env` file in the application root directory:

```
SECRET_KEY=your-super-secure-secret-key
FLASK_CONFIG=production
```

### 6. Configure Nginx

1. Copy the provided `nginx_cookiemgr.conf` to `/etc/nginx/sites-available/`:

```bash
sudo cp nginx_cookiemgr.conf /etc/nginx/sites-available/cookiemgr
```

2. Edit the configuration to match your domain and file paths:

```bash
sudo nano /etc/nginx/sites-available/cookiemgr
```

3. Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/cookiemgr /etc/nginx/sites-enabled/
sudo nginx -t  # Test the configuration
sudo systemctl restart nginx
```

### 7. Set Up SSL (Optional but Recommended)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d cookiemgr.yourdomain.com
```

### 8. Configure systemd Service

1. Copy the provided `cookiemgr.service` to systemd:

```bash
sudo cp cookiemgr.service /etc/systemd/system/
```

2. Edit the service file to match your paths:

```bash
sudo nano /etc/systemd/system/cookiemgr.service
```

3. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cookiemgr
sudo systemctl start cookiemgr
```

### 9. Set Up Automated Backups

1. Copy the provided `backup.sh` script to a suitable location:

```bash
sudo cp backup.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/backup.sh
```

2. Edit the script to match your paths:

```bash
sudo nano /usr/local/bin/backup.sh
```

3. Set up a cron job to run daily backups:

```bash
sudo crontab -e
```

Add the following line to run the backup daily at 2 AM:

```
0 2 * * * /usr/local/bin/backup.sh
```

## Maintenance

### Updating the Application

```bash
cd /path/to/cookiemgr
git pull
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
sudo systemctl restart cookiemgr
```

### Monitoring Logs

```bash
# View application logs
sudo journalctl -u cookiemgr

# View Nginx access logs
sudo tail -f /var/log/nginx/access.log

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Manual Backup

```bash
sudo /usr/local/bin/backup.sh
```

## Troubleshooting

### Application Won't Start

1. Check the logs:
   ```bash
   sudo journalctl -u cookiemgr -n 100
   ```

2. Verify the configuration:
   ```bash
   sudo systemctl status cookiemgr
   ```

3. Check file permissions:
   ```bash
   sudo chown -R www-data:www-data /path/to/cookiemgr
   ```

### Database Errors

1. Check if the database file exists:
   ```bash
   ls -la /path/to/cookiemgr/instance/db.sqlite3
   ```

2. Verify database permissions:
   ```bash
   sudo chown www-data:www-data /path/to/cookiemgr/instance/db.sqlite3
   sudo chmod 664 /path/to/cookiemgr/instance/db.sqlite3
   ```

### Nginx Errors

1. Test the Nginx configuration:
   ```bash
   sudo nginx -t
   ```

2. Check if Nginx is running:
   ```bash
   sudo systemctl status nginx
   ```

## Security Considerations

1. Keep the system updated:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Use a firewall:
   ```bash
   sudo ufw allow 'Nginx Full'
   sudo ufw allow ssh
   sudo ufw enable
   ```

3. Use strong passwords and secure the `.env` file:
   ```bash
   sudo chmod 600 /path/to/cookiemgr/.env
   sudo chown www-data:www-data /path/to/cookiemgr/.env
   ```
