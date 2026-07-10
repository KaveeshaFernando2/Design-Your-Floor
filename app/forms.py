from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    
    role = SelectField(
        'Role',
        choices=[
            ('customer','Customer'), 
            ('supplier','Supplier'), 
            ('vendor','Vendor'), 
            ('mason','Mason'), 
            ('delivery','Delivery')
        ],
        default='customer',
        validators=[DataRequired()]
    )
    
    phone = StringField('Phone', validators=[Length(max=30)])
    city = StringField('City', validators=[Length(max=100)])
    
    # Supplier-specific fields
    company_name = StringField('Company Name', validators=[Optional(), Length(max=150)])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    
    submit = SubmitField('Register')
