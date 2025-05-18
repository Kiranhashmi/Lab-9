from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Regexp
import bleach
import secrets

# Generate a secure secret key
secret_key = secrets.token_hex(32)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret_key  # Using generated secret key

db = SQLAlchemy(app)


class UserForm(FlaskForm):
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(min=1, max=100),
        Regexp(r'^[a-zA-Z\- ]+$', message="Only letters, spaces and hyphens allowed")
    ])
    last_name = StringField('Last Name', validators=[
        Length(max=100),
        Regexp(r'^[a-zA-Z\- ]*$', message="Only letters, spaces and hyphens allowed")
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, max=100)
    ])


class User(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'{self.sno} - {self.first_name}'


def sanitize_input(input_string):
    return bleach.clean(input_string, strip=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = UserForm()

    if form.validate_on_submit():
        try:
            new_user = User(
                first_name=sanitize_input(form.first_name.data),
                last_name=sanitize_input(form.last_name.data),
                email=sanitize_input(form.email.data),
                password=form.password.data  # Note: In production, hash this!
            )
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    users = User.query.all()
    return render_template('index.html', form=form, users=users)


@app.route('/delete/<int:sno>', methods=['POST'])
def delete_user(sno):
    try:
        user_to_delete = User.query.get_or_404(sno)
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('index'))


@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update_user(sno):
    user = User.query.get_or_404(sno)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        try:
            user.first_name = sanitize_input(form.first_name.data)
            user.last_name = sanitize_input(form.last_name.data)
            user.email = sanitize_input(form.email.data)
            user.password = form.password.data  # Note: In production, hash this!
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('update.html', form=form, user=user)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
