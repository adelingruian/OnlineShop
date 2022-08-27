from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField, EmailField, SelectField, FileField
from wtforms.validators import DataRequired, URL, Email, ValidationError
from flask_ckeditor import CKEditorField

def is_integer(form, field):
    if field.data != "":
        try:
            int(field.data)
        except ValueError:
            raise ValidationError('Invalid quantity')

def is_float(form, field):
    if field.data != "":
        try:
            float(field.data)
        except ValueError:
            raise ValidationError('Invalid price formating')


class AddItemForm(FlaskForm):
    name = StringField(label="Product name:", validators=[DataRequired()])
    price = StringField("Price:", validators=[DataRequired(), is_float])
    sale_price = StringField("Sale price (only if product on sale):", validators=[is_float])
    description = CKEditorField("Decription", validators=[DataRequired()])
    s = StringField("Size 'S' quantity:", validators=[is_integer])
    m = StringField("Size 'M' quantity:", validators=[is_integer])
    l = StringField("Size 'L' quantity:", validators=[is_integer])
    xl = StringField("Size 'XL' quantity:", validators=[is_integer])
    main_image = FileField("Main image:", validators=[DataRequired()])
    image1 = FileField("Additional image 1:")
    image2 = FileField("Additional image 2:")
    image3 = FileField("Additional image 3:")
    submit = SubmitField("Submit")


class RegisterForm(FlaskForm):
    name = StringField("Name:", validators=[DataRequired()])
    surname = StringField("Surname:", validators=[DataRequired()])
    email = StringField("E-mail:", validators=[DataRequired(), Email()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("E-mail:", validators=[DataRequired(), Email()])
    password = PasswordField("Password:", validators=[DataRequired()])
    submit = SubmitField("Login")



