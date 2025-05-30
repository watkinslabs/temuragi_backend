from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Optional, URL, Length

class MenuItemForm(FlaskForm):
    """Form for regular menu items"""
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    icon = SelectField('Icon', validators=[DataRequired()])
    link = StringField('Link URL', validators=[DataRequired(), Length(max=255)])
    parent_id = SelectField('Parent', coerce=int, validators=[Optional()])
    is_visible = BooleanField('Visible in menu', default=True)
    open_new_tab = BooleanField('Open in new tab', default=False)
    order = IntegerField('Order', default=0, validators=[Optional()])

class CategoryForm(FlaskForm):
    """Form for menu categories"""
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    icon = SelectField('Icon', validators=[DataRequired()])
    link = StringField('Link URL', validators=[Optional(), Length(max=255)])
    parent_id = SelectField('Parent', coerce=int, validators=[Optional()])
    is_visible = BooleanField('Visible in menu', default=True)
    order = IntegerField('Order', default=0, validators=[Optional()])