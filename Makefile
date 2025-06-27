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

preview-order:
	@python -m app.cli database  preview-order

list-tables:
	@python -m app.cli database  list-tables

create-db:
	@python -m app.cli database  create temuragi

drop-db:
	@python -m app.cli database  drop temuragi

create-tables:
	
	@python -m app.cli database  create-tables

drop-tables:
	@python -m app.cli database  drop-tables

create-data:
	@python -m app.cli database  create-initial-data



rebuild-db: drop-tables create-tables import-data permission 

import-data:
	@python -m app.cli porter import-dir ./data



permission: 
	@python -m app.cli permission add '*' '*' '*'
	@python -m app.cli permission grant admin '*:*:*'
	

templates: theme page db-type site-config site-prefix site-tag site-keyword  page-fragment template-fragment report
	@python -m app.cli model_report generate Template -c SYSTEM --slug 'template/list' --name 'Manage Templates' --description 'UI/HTML Fragments for system design' --system 
	@python -m app.cli form report-datatable template/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both Template

	@python -m app.cli model_report generate User -c SYSTEM --slug 'user/list' --name 'Manage User' --description 'Profile configuration' --system 
	@python -m app.cli form report-datatable user/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both User

	@python -m app.cli model_report generate Role -c SYSTEM --slug 'role/list' --name 'Manage Role' --description 'User feature grouping' --system 
	@python -m app.cli form report-datatable role/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both Role

	@python -m app.cli model_report generate Permission -c SYSTEM --slug 'permission/list' --name 'Manage Permission' --description 'RBAC Permissions' --system 
	@python -m app.cli form report-datatable permission/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both Permission

	@python -m app.cli model_report generate RolePermission -c SYSTEM --slug 'rolepermission/list' --name 'Manage RolePermission' --description 'Assign features to a role' --system 
	@python -m app.cli form report-datatable rolepermission/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both RolePermission
	
	@python -m app.cli model_report generate Connection -c SYSTEM --slug 'connection/list' --name 'Manage Database Connections' --description 'System integrations into data sources' --system 
	@python -m app.cli form report-datatable connection/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both Connection

	@python -m app.cli model_report generate VariableType -c SYSTEM --slug 'variabletype/list' --name 'Manage Variable Types' --description 'Report Variable representations' --system 
	@python -m app.cli form report-datatable variabletype/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both VariableType

	@python -m app.cli model_report generate DataType -c SYSTEM --slug 'datatype/list' --name 'Manage Report Data Types' --description 'Report data represention' --system 
	@python -m app.cli form report-datatable datatype/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both DataType


	@python -m app.cli model_report generate Module -c SYSTEM --slug 'module/list' --name 'Manage Module' --description 'Module specific configurations' --system 
	@python -m app.cli form report-datatable module/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both Module


theme:
	@python -m app.cli model_report generate Theme -c SYSTEM --slug 'theme/list' --name 'Manage Themes' --description 'System Themes' --system 
	@python -m app.cli form report-datatable theme/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both Theme

page:
	@python -m app.cli model_report generate Page -c SYSTEM --slug 'page/list' --name 'Manage Pages' --description 'System Pages' --system 
	@python -m app.cli form report-datatable page/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both Page


db-type:
	@python -m app.cli model_report generate DatabaseType -c SYSTEM --slug 'databasetype/list' --name 'Manage Module' --description 'Module specific configurations' --system 
	@python -m app.cli form report-datatable databasetype/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both DatabaseType

page-fragment:
	@python -m app.cli model_report generate PageFragment -c SYSTEM --slug 'pagefragment/list' --name 'Page Fragment Module' --description 'PAge Content' --system 
	@python -m app.cli form report-datatable pagefragment/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix site_module_ --mode both PageFragment

template-fragment:
	@python -m app.cli model_report generate TemplateFragment -c SYSTEM --slug 'templatefragment/list' --name 'Tempalte Fragment Module' --description 'Tempalte content' --system 
	@python -m app.cli form report-datatable templatefragment/list
	@python -m app.cli form generate --no-optional-badge  --create-page --prefix tpl_ --mode both TemplateFragment

site-tag:
	@python -m app.cli model_report generate SiteTag -c SYSTEM --slug 'sitetag/list' --name 'Manage Site Tag' --description 'Site tag configurations' --system
	@python -m app.cli form report-datatable sitetag/list
	@python -m app.cli form generate --no-optional-badge --create-page --prefix site_tag_ --mode both SiteTag

site-keyword: 
	@python -m app.cli model_report generate SiteKeyword -c SYSTEM --slug 'sitekeyword/list' --name 'Manage Site Keyword' --description 'Site keyword configurations' --system
	@python -m app.cli form report-datatable sitekeyword/list
	@python -m app.cli form generate --no-optional-badge --create-page --prefix site_keyword_ --mode both SiteKeyword


site-prefix:
	@python -m app.cli model_report generate SitePrefix -c SYSTEM --slug 'siteprefix/list' --name 'Manage Site Prefix' --description 'Site prefix configurations' --system
	@python -m app.cli form report-datatable siteprefix/list
	@python -m app.cli form generate --no-optional-badge --create-page --prefix site_prefix_ --mode both SitePrefix

site-config:
	@python -m app.cli model_report generate SiteConfig -c SYSTEM --slug 'siteconfig/list' --name 'Manage Site Config' --description 'Site specific configurations' --system
	@python -m app.cli form report-datatable siteconfig/list
	@python -m app.cli form generate --no-optional-badge --create-page --prefix site_config_ --mode both SiteConfig

report:
	@python -m app.cli model_report generate Report -c SYSTEM --slug 'report2/list' --name 'Manage Report Defiunitions' --description 'Template metadata specific configurations' --system
	@python -m app.cli form report-datatable report2/list
	
	