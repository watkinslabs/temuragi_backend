# Makefile for installing and restarting temuragi services

# variables
config_dir := config
nginx_conf_src := $(config_dir)/etc/nginx/conf.d/temuragi.conf
nginx_conf_dest := /etc/nginx/conf.d/temuragi.conf

systemd_service_src := $(config_dir)/etc/systemd/system/temuragi.service
systemd_service_dest := /etc/systemd/system/temuragi.service

uwsgi_ini_src := $(config_dir)/uwsgi.ini
uwsgi_ini_dest := /web/temuragi/config/uwsgi.ini

# phony targets
.PHONY: all install install_nginx install_systemd restart restart_nginx restart_uwsgi enable_services

all: install restart

install: install_nginx install_systemd enable_services

install_nginx:
	install -m 644 $(nginx_conf_src) $(nginx_conf_dest)

install_systemd:
	install -m 644 $(systemd_service_src) $(systemd_service_dest)
	systemctl daemon-reload

install_uwsgi:
	install -m 644 $(uwsgi_ini_src) $(uwsgi_ini_dest)

enable_services:
	systemctl enable nginx
	systemctl enable temuragi.service

restart: restart_nginx restart_uwsgi

restart_nginx:
	systemctl restart nginx

restart_uwsgi:
	systemctl restart temuragi.service

firewall:
	@python -m app.admin.firewall.firewall_cli