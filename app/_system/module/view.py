# module_config/view.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, g, json

from app.models import Module

bp = Blueprint('module_config', __name__, url_prefix="/module-config", template_folder="tpl")

@bp.before_request
def bind_session():
    """Ensure session is available for every request in this blueprint"""
    if not hasattr(g, 'session'):
        g.session = current_app.db_session

@bp.teardown_request
def close_session(exc):
    """Close session after request is done"""
    sess = g.pop('session', None)
    if sess:
        sess.close()

@bp.route('/', methods=['GET'])
def home():
    """Main module configuration management page"""
    db_session = g.session
    configs = Module.get_all_configs(db_session)
    return render_template('module_config/home.html', configs=configs)

@bp.route('/add', methods=['GET', 'POST'])
def add_config():
    """Add a new module configuration"""
    if request.method == 'POST':
        module_name = request.form.get('module_name', '').strip()
        is_active = request.form.get('is_active') == 'on'
        config_json = request.form.get('config_data', '{}')
        
        if not module_name:
            flash('Module name cannot be empty', 'error')
            return redirect(url_for('module_config.add_config'))
        
        # Validate JSON
        try:
            config_dict = json.loads(config_json)
        except json.JSONDecodeError:
            flash('Invalid JSON configuration', 'error')
            return render_template('module_config/edit.html', 
                                  config=None, 
                                  module_name=module_name,
                                  is_active=is_active,
                                  config_data=config_json)
        
        db_session = g.session
        success, message = Module.add_or_update_config(db_session, module_name, config_dict, is_active)
        
        flash(message, 'success' if success else 'error')
        if success:
            return redirect(url_for('module_config.home'))
        else:
            return render_template('module_config/edit.html', 
                                  config=None, 
                                  module_name=module_name,
                                  is_active=is_active,
                                  config_data=config_json)
    
    # GET request
    return render_template('module_config/edit.html', 
                          config=None, 
                          module_name='',
                          is_active=True,
                          config_data='{}')

@bp.route('/edit/<uuid:config_id>', methods=['GET', 'POST'])
def edit_config(config_id):
    """Edit an existing module configuration"""
    db_session = g.session
    config = Module.get_config_by_id(db_session, config_id)
    
    if not config:
        flash('Configuration not found', 'error')
        return redirect(url_for('module_config.home'))
    
    if request.method == 'POST':
        module_name = request.form.get('module_name', '').strip()
        is_active = request.form.get('is_active') == 'on'
        config_json = request.form.get('config_data', '{}')
        
        if not module_name:
            flash('Module name cannot be empty', 'error')
            return redirect(url_for('module_config.edit_config', config_id=config_id))
        
        # Validate JSON
        try:
            config_dict = json.loads(config_json)
        except json.JSONDecodeError:
            flash('Invalid JSON configuration', 'error')
            return render_template('module_config/edit.html', 
                                  config=config,
                                  module_name=module_name,
                                  is_active=is_active,
                                  config_data=config_json)
        
        # Update config object
        config.module_name = module_name
        config.is_active = is_active
        config.set_config_dict(config_dict)
        
        try:
            db_session.commit()
            flash('Configuration updated successfully', 'success')
            return redirect(url_for('module_config.home'))
        except Exception as e:
            db_session.rollback()
            flash(f'Error updating configuration: {str(e)}', 'error')
            return render_template('module_config/edit.html', 
                                  config=config,
                                  module_name=module_name,
                                  is_active=is_active,
                                  config_data=config_json)
    
    # GET request
    return render_template('module_config/edit.html', 
                          config=config,
                          module_name=config.module_name,
                          is_active=config.is_active,
                          config_data=json.dumps(config.get_config_dict(), indent=2))

@bp.route('/toggle/<uuid:config_id>', methods=['POST'])
def toggle_config(config_id):
    """Toggle a module configuration's active status"""
    db_session = g.session
    config = Module.get_config_by_id(db_session, config_id)
    
    if not config:
        flash('Configuration not found', 'error')
        return redirect(url_for('module_config.home'))
    
    if config.is_active:
        success, message = Module.deactivate_config(db_session, config_id)
    else:
        success, message = Module.activate_config(db_session, config_id)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('module_config.home'))

@bp.route('/delete/<uuid:config_id>', methods=['POST'])
def delete_config(config_id):
    """Delete a module configuration"""
    db_session = g.session
    success, message = Module.delete_config(db_session, config_id)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('module_config.home'))