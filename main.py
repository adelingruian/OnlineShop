from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_bootstrap import Bootstrap
from forms import AddItemForm, LoginForm, RegisterForm
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import os
import stripe

app = Flask(__name__)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
app.config['SECRET_KEY'] = "Random Text"
db = SQLAlchemy(app)

ckeditor = CKEditor(app)

UPLOAD_FOLDER = "static/images/"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

stripe.api_key = 'sk_test_51LbKMDLFwmEu37mfNzlusYBqfs8FeP6kbrgzozWnAxk2Svq6NrS0iSKqhpAMWxPpmZjBSvOAVOgjJIuFk0yCUPe300HxQEGLau'


login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    surname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    pass_hash = db.Column(db.String(50), nullable=False)
    admin = db.Column(db.Boolean, default=False)
    order = relationship("UserOrder", back_populates="user", uselist=False)


class UserOrder(db.Model):
    __tablename__ = "user_orders"
    id = db.Column(db.Integer, primary_key=True)
    orderlines = relationship("OrderLine", back_populates="order")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = relationship("User", back_populates="order")


class OrderLine(db.Model):
    __tablename__ = "orderlines"
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    item = relationship("Item", back_populates="orderline")
    order_id = db.Column(db.Integer, db.ForeignKey("user_orders.id"))
    order = relationship("UserOrder", back_populates="orderlines")


class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    sale_price = db.Column(db.Float)
    description = db.Column(db.String(300), nullable=False)
    stripe_product = db.Column(db.String(30), nullable=False)
    stripe_price = db.Column(db.String(30), nullable=False)
    size = relationship("Size", back_populates="item", uselist=False)
    images = relationship("Images", back_populates="item", uselist=False)
    orderline = relationship("OrderLine", back_populates="item")


class Size(db.Model):
    __tablename__ = "sizes"
    id = db.Column(db.Integer, primary_key=True)
    s = db.Column(db.Integer, default=0)
    m = db.Column(db.Integer, default=0)
    l = db.Column(db.Integer, default=0)
    xl = db.Column(db.Integer, default=0)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"),)
    item = relationship("Item", back_populates="size", uselist=False)


class Images(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    main_image = db.Column(db.String(30))
    image1 = db.Column(db.String(30), default="")
    image2 = db.Column(db.String(30), default="")
    image3 = db.Column(db.String(30), default="")
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    item = relationship("Item", back_populates="images", uselist=False)


db.create_all()

# user = User (
#     name="Adelin",
#     surname="Gruian",
#     email="aa.gruian@gmail.com",
#     pass_hash="noneed",
# )
# db.session.add(user)
# db.session.commit()
user = User.query.filter_by(email="aa.gruian@gmail.com").first()


def save_image(image):

    def allowed_file(name):
        return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    filename = secure_filename(image.filename)
    if allowed_file(image.filename):
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


@app.route('/')
def index():
    list_of_items = Item.query.all()
    return render_template("index.html", items=list_of_items)


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()

    if register_form.validate_on_submit():
        if User.query.filter_by(email=register_form.email.data).first() is None:
            user_to_register = User(
                name=register_form.name.data,
                surname=register_form.surname.data,
                email=register_form.email.data,
                pass_hash=generate_password_hash(register_form.password.data, "pbkdf2:sha256", 8)
            )
            print("watever")
            db.session.add(user_to_register)
            db.session.commit()
            login_user(user_to_register)
            return redirect(url_for('index'))
        else:
            url = url_for('login')
            flash(f'User already exists.<a href="{url}">Login here</a>')
    return render_template('register.html', form=register_form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user_to_login = User.query.filter_by(email=login_form.email.data).first()
        if not user:
            url = url_for('register')
            flash(f'User is not registered. <a href="{url}">Register here</a>')
        elif check_password_hash(user.pass_hash, login_form.password.data):
            login_user(user_to_login)
            return redirect(url_for('index'))
        else:
            flash("Wrong password.")
    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/item/<item_id>', methods=['GET', 'POST'])
def item(item_id):
    selected_item = Item.query.get(item_id)
    # ADDING ITEM TO CART
    if request.method == 'POST':
        if current_user.order is None:
            user_order = UserOrder(
                user=current_user
            )
            db.session.add(user_order)
            db.session.commit()
        else:
            # CREATE AN ORDER IF ONE DOES NOT EXIST
            user_order = UserOrder.query.get(current_user.get_id())

        # FORMATING VARIABLES FROM FORM
        btnradio = request.form['btnradio']
        if request.form['quantity'] == "":
            quantity_requested = 1
        else:
            quantity_requested = int(request.form['quantity'])

        # CHECK IF THERE IS ENOUGH QUANTITY OF THE SIZE REQUESTED.
        if btnradio == "s":
            if selected_item.size.s < quantity_requested:
                print('Code was here')
                flash(f"There are only {selected_item.size.s} pieces left from size {btnradio.upper()}.")
                return redirect(url_for('item', item_id=item_id))
        elif btnradio == "m":
            if selected_item.size.m < quantity_requested:
                print('Code was here')
                flash(f"There are only {selected_item.size.m} pieces left from size {btnradio.upper()}.")
                return redirect(url_for('item', item_id=item_id))
        elif btnradio == "l":
            if selected_item.size.l < quantity_requested:
                print('Code was here')
                flash(f"There are only {selected_item.size.l} pieces left from size {btnradio.upper()}.")
                return redirect(url_for('item', item_id=item_id))
        elif btnradio == "xl":
            if selected_item.size.xl < quantity_requested:
                print('Code was here')
                flash(f"There are only {selected_item.size.xl} pieces left from size {btnradio.upper()}.")
                return redirect(url_for('item', item_id=item_id))

        #CHECK IF ITEM ALREADY IN SHOPING CART
        if OrderLine.query.filter_by(item=selected_item, size=btnradio).first():
            order_line = OrderLine.query.filter_by(item=selected_item, size=btnradio).first()
            order_line.quantity += quantity_requested
        else:
            new_order_line = OrderLine(
                size=btnradio,
                quantity=quantity_requested,
                item=selected_item,
                order=user_order,
            )
            db.session.add(new_order_line)
        db.session.commit()

        return redirect(url_for('shoping_cart'))

    return render_template("item.html", item=selected_item)


@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    add_item_form = AddItemForm()
    if request.method == 'POST':
        print('DA')
        print(add_item_form.validate_on_submit())
    if add_item_form.validate_on_submit():
        if add_item_form.sale_price.data:
            sale_price = add_item_form.sale_price.data
            price_for_stripe = int(sale_price) * 100
        else:
            sale_price = None
            price_for_stripe = int(add_item_form.price.data) * 100

        new_stripe_product = stripe.Product.create(name=add_item_form.name.data,
                                                   description=add_item_form.description.data,
                                                   images=[f"images/{add_item_form.main_image.data.filename}"])
        new_stripe_price = stripe.Price.create(unit_amount=price_for_stripe,
                                               currency="ron",
                                               product=new_stripe_product.id)
        new_item = Item(
            name=add_item_form.name.data,
            price=add_item_form.price.data,
            sale_price=sale_price,
            description=add_item_form.description.data,
            stripe_product=new_stripe_product.id,
            stripe_price=new_stripe_price.id,
        )
        db.session.add(new_item)

        new_size = Size(
            s=add_item_form.s.data,
            m=add_item_form.m.data,
            l=add_item_form.l.data,
            xl=add_item_form.xl.data,
            item=new_item,
        )
        db.session.add(new_size)

        main_image = add_item_form.main_image.data
        image1 = add_item_form.image1.data
        image2 = add_item_form.image2.data
        image3 = add_item_form.image3.data
        save_image(main_image)
        save_image(image1)
        save_image(image2)
        save_image(image3)

        new_images = Images(
            main_image=f"images/{main_image.filename}",
            image1=f"images/{image1.filename}",
            image2=f"images/{image2.filename}",
            image3=f"images/{image3.filename}",
            item=new_item,
        )
        db.session.add(new_images)

        db.session.commit()

        # TODO MAKE A REDIRECT AFTER SUCCESFULY ADDED NEW ITEM
        return "Succes"

    return render_template('add_item.html', form=add_item_form)


@app.route('/shoping-cart')
def shoping_cart():
    print(User.query.get(current_user.get_id()).surname)
    order_id = UserOrder.query.filter_by(user_id=current_user.get_id()).first().id
    order_lines = OrderLine.query.filter_by(order_id=order_id).all()

    return render_template("shoping-cart.html", order_lines=order_lines)


@app.route('/shoping-cart/edit', methods=['GET', 'POST'])
def edit_from_cart():
    order_line_id = request.args.get('order_line_id')
    item_to_edit = OrderLine.query.get(order_line_id).item
    db.session.delete(OrderLine.query.get(order_line_id))
    db.session.commit()

    return redirect(url_for('item', item_id=item_to_edit.id))


@app.route('/shoping-cart/delete', methods=['GET', 'POST'])
def delete_from_cart():
    order_line_id = request.args.get('order_line_id')
    selected_orderline = OrderLine.query.get(order_line_id)
    db.session.delete(selected_orderline)
    db.session.commit()

    return redirect(url_for('shoping_cart'))


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/cancel')
def cancel():
    return render_template('cancel.html')



@app.route('/create-checkout-session', methods=['GET', 'POST'])
def create_checkout_session():

    order_id = UserOrder.query.filter_by(user_id=current_user.get_id()).first().id
    order_lines = OrderLine.query.filter_by(order_id=order_id).all()

    list_of_dict = []

    for orderline in order_lines:
        new_dict_item = {
            'price': orderline.item.stripe_price,
            'quantity': orderline.quantity,
        }
        list_of_dict.append(new_dict_item)

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=list_of_dict,
            mode='payment',
            success_url="http://127.0.0.1:5000/success",
            cancel_url="http://127.0.0.1:5000/cancel",
        )
    except Exception as e:
        return str(e)

    return redirect(checkout_session.url, code=303)






if __name__ == '__main__':
    app.run()
