from cassandra import cluster
from cassandra.cluster import Cluster
from flask import *
from flask_mail import *
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
from setting import cassandra_connect
import os
import math
import random
from werkzeug.utils import secure_filename
from datetime import date
from datetime import datetime

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'cn754879@gmail.com'
app.config['MAIL_PASSWORD'] = 'banve12kmt'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
Bootstrap(app)


mail = Mail(app)


def generateOTP():

    digits = "0123456789"
    OTP = ""
    for i in range(4):
        OTP += digits[math.floor(random.random() * 10)]

    return OTP


@app.route('/login', methods=['GET', 'POST'])
def login():
    if(request.method == "GET"):
        return render_template("login.html")
    if(request.method == "POST"):
        email = request.form['email']
        password = request.form['password']
        session = cassandra_connect()
        session.execute('USE "icecream"')
        rows = session.execute(
            """
        SELECT email,password,user_type FROM users WHERE email = %(em)s
        """, {'em': email})
        if(rows):
            if(rows[0].password == password):
                if(rows[0].user_type == "customer"):
                    resp = make_response(redirect("/"))
                    resp.set_cookie('user', email)
                    return resp
                if(rows[0].user_type == "admin"):
                    resp = make_response(redirect("/admin_home"))
                    resp.set_cookie('usera', email)
                    return resp
            else:
                return render_template("login.html", message="Wrong Password.", status=-1)
        else:
            return render_template("login.html", message="User Account doesn't exist.", status=-1)


@app.route('/logout')
def logout():
    resp = make_response(render_template(
        'login.html', message="Successful Logout.", status=1))
    resp.set_cookie('user', '', expires=0)
    return resp


@app.route('/user/id=<id>', methods=['GET', 'POST'])
def user(id):
    if(request.cookies.get('user')):
        session = cassandra_connect()
        session.execute('USE "icecream"')
        row = session.execute(
            """
        SELECT name,mobile,address,email FROM users WHERE email = %(em)s
        """, {'em': id})
        return render_template('profile.html', valu=row, user=row[0].name, email=row[0].email)
    else:
        return make_response(redirect("/"))


@app.route('/buy/id=<id>', methods=['GET', 'POST'])
def buy(id):
    if(request.method == "GET"):
        if(request.cookies.get('user')):
            session = cassandra_connect()
            session.execute('USE "icecream"')
            email = request.cookies.get('user')
            ur = session.execute(
                """
            SELECT name,mobile,address,email FROM users WHERE email = %(em)s
            """, {'em': email})
            prod = session.execute(
                """
            SELECT prod_id, prod_name, prod_type, quantity, man_date, exp_date, batch_no, rate,img_name FROM product WHERE prod_id=%(id)s
            """, {'id': int(id)})
            return render_template('order.html', userf=0, prod=prod, quan=0, invoice=0, date=0, user=ur[0].name, email=email)
        else:
            return render_template("login.html", message="Please, login first.", status=-1)
    if(request.method == "POST"):
        value = request.form['fp']
        if(int(value) == 300):
            quantity = request.form['quantity']
            email = request.cookies.get('user')
            session = cassandra_connect()
            session.execute('USE "icecream"')
            ur = session.execute(
                """
            SELECT name,mobile,address,email FROM users WHERE email = %(em)s
            """, {'em': email})
            prod = session.execute(
                """
            SELECT prod_id, prod_name, prod_type, quantity, man_date, exp_date, batch_no, rate,img_name FROM product WHERE prod_id=%(id)s
            """, {'id': int(id)})
            invoice = session.execute("""
            SELECT value FROM flag WHERE forname= %(inv)s
            """, {'inv': "invoice"})
            today = date.today()
            now = datetime.now()
            session.execute(
                """
            INSERT INTO orders (invoice_no, amount, c_id, date, p_id, quantity,time,p_name)  
            VALUES(%(inv)s,%(amt)s,%(cid)s,%(date)s,%(pid)s,%(quan)s,%(time)s,%(pname)s)
            """, {'inv': int(invoice[0].value), 'amt': (int(quantity)*int(prod[0].rate)), 'cid': ur[0].email, 'date': today, 'pid': prod[0].prod_id, 'quan': int(quantity), 'time': now.strftime("%H:%M:%S"), 'pname': prod[0].prod_name})
            msg = Message(
                'Order No.'+str(invoice[0].value), sender='nkamath001@gmail.com', recipients=[ur[0].email])
            msg.body = "Dear <b>%s</b>, <br>This message is sent from ICMS web application developed using Flask. <br>Your order has been received will be delivered in 7 working days.<br><hr><b>Order Details</b><hr>Date - <b>%s</b><br>Order No - <b>%s</b><br>Product Name - <b>%s</b><br>Quantity - <b>%s</b><hr>Total Amount - <b>%s/-</b><hr><br>Thank You for purchasing from our website.<br><br><b>ICMS</b>" % (
                (ur[0].name), today.strftime("%B %d, %Y"), invoice[0].value, prod[0].prod_name, int(quantity), (int(quantity)*int(prod[0].rate)))
            msg.html = "Dear <b>%s</b>, <br>This message is sent from ICMS web application developed using Flask. <br>Your order has been received will be delivered in 7 working days.<br><hr><b>Order Details</b><hr>Date - <b>%s</b><br>Order No - <b>%s</b><br>Product Name - <b>%s</b><br>Quantity - <b>%s</b><hr>Total Amount - <b>%s/-</b><hr><br>Thank You for purchasing from our website.<br><br><b>ICMS</b>" % (
                (ur[0].name), today.strftime("%B %d, %Y"), invoice[0].value, prod[0].prod_name, int(quantity), (int(quantity)*int(prod[0].rate)))
            mail.send(msg)
            session.execute(
                """
            UPDATE flag SET value = %(val)s WHERE forname = %(forname)s
            """, {'val': int(invoice[0].value)+1, 'forname': "invoice"})
            session.execute(
                """
            UPDATE product SET quantity = %(quan)s WHERE prod_id = %(pid)s
            """, {'quan': int(prod[0].quantity)-int(quantity), 'pid': int(prod[0].prod_id)})
            return render_template('order.html', userf=ur, prod=prod, quan=int(quantity), invoice=int(invoice[0].value), date=today.strftime("%B %d, %Y"), user=ur[0].name, email=ur[0].email)


@app.route('/')
def home():
    session = cassandra_connect()
    session.execute('USE "icecream"')
    rows = session.execute(
        'SELECT prod_id, prod_name, prod_type, quantity, man_date, exp_date, batch_no, rate,img_name FROM product')
    if(request.cookies.get('user')):
        email = request.cookies.get('user')
        row = session.execute(
            """
        SELECT name FROM users WHERE email = %(em)s
        """, {'em': email})
        if(row):
            return render_template('home.html', op=rows, user=row[0].name, email=email)
        else:
            return render_template('home.html', op=rows, user=0, email=0)
    else:
        return render_template('home.html', op=rows, user=0, email=0)


@app.route('/myorders', methods=['GET', 'POST'])
def my_orders():
    if(request.cookies.get('user')):
        email = request.cookies.get('user')
        session = cassandra_connect()
        session.execute('USE "icecream"')
        orders = session.execute(
            """SELECT invoice_no, amount, c_id, date, p_id, quantity,time,p_name FROM orders where c_id=%(id)s ALLOW FILTERING""", {'id': email})
        row = session.execute(
            """SELECT name FROM users WHERE email = %(em)s""", {'em': email})
        return render_template('my_orders.html', orders=orders, email=email, user=row[0].name)
    else:
        return make_response(redirect("/"))


@app.route('/forget_pass', methods=['GET', 'POST'])
def forget_pass():

    if request.method == "GET":
        return render_template("forget_pass.html", s1=1, s2=0, s3=0)
    if request.method == "POST":
        id = request.form['fp']

        if(id == "200"):
            email = request.form['email']
            session = cassandra_connect()
            session.execute('USE "icecream"')
            rows = session.execute(
                """
            SELECT name FROM users WHERE email = %(em)s
            """, {'em': email})
            if(rows):
                otp = generateOTP()
                msg = Message('OTP', sender='nkamath001@gmail.com',
                              recipients=[email])
                msg.body = "Dear <b>%s</b>,<br>This message is sent from ICMS web application developed using Flask.<br> Your OTP for resetting password is <b>%s</b>.<br><b>ICMS</b>" % (
                    (rows[0].name), otp)
                msg.html = "Dear <b>%s</b>,<br>This message is sent from ICMS web application developed using Flask.<br> Your OTP for resetting password is <b>%s</b>.<br><b>ICMS</b>" % (
                    (rows[0].name), otp)
                mail.send(msg)
                resp = make_response(render_template(
                    "forget_pass.html", s1=0, s2=1, s3=0))
                resp.set_cookie('email', email)
                resp.set_cookie('otp', otp)
                return resp
            else:
                return render_template("login.html", message="Reset not possible User doesn't exist try again.", status=-1)

        elif(id == "third"):
            ent_otp = int(request.form['otp'])
            o_otp = int(request.cookies.get('otp'))

            if(ent_otp == o_otp):
                return render_template("forget_pass.html", s1=0, s2=0, s3=1)
            else:
                return render_template("login.html", message="Reset not possible otp doesn't match try again.", status=-1)

        if(id == "400"):
            passwd = request.form['psw']
            email = request.cookies.get('email')
            session = cassandra_connect()
            session.execute('USE "icecream"')
            session.execute(
                """
            UPDATE users SET password = %(psw)s WHERE email = %(email)s
            """, {'psw': passwd, 'email': email})
            return render_template("login.html", message="Password Reset successfully", status=1)


@app.route('/registration', methods=['GET', 'POST'])
def reg():
    if request.method == "GET":
        return render_template("registartion.html")
    if request.method == "POST":
        name = request.form['name']
        mobile = int(request.form['mobile'])
        email = request.form['email']
        address = request.form['address']
        password = request.form['psw']
        psw_repeat = request.form['psw_repeat']

        if(password != psw_repeat):
            return render_template("registartion.html", status=-1, message="Passwords doesn't match")
        else:
            session = cassandra_connect()
            session.execute('USE "icecream"')
            session.execute(
                """
            INSERT INTO users (email, name, address, mobile, password, user_type)  
            VALUES(%(email)s,%(name)s,%(address)s,%(mobile)s,%(password)s,%(user_type)s)
            """, {'email': email, 'name': name, 'address': address, 'mobile': mobile, 'password': password, 'user_type': "customer"})
            return render_template("login.html", message="Successfully Account Created.", status=1)


@app.route('/admin_home')
def admin_home():
    if(request.cookies.get('usera')):
        session = cassandra_connect()
        session.execute('USE "icecream"')
        rows = session.execute(
            'SELECT prod_id, prod_name, prod_type, quantity, man_date, exp_date, batch_no, rate,img_name FROM product')
        return render_template('admin_home.html', op=rows)
    else:
        return render_template("login.html", message="Unauthorized Action.", status=-1)


@app.route('/logout_admin')
def logout_admin():
    resp = make_response(render_template(
        'login.html', message="Successful Logout.", status=1))
    resp.set_cookie('usera', '', expires=0)
    return resp


@app.route('/orderlist')
def orderlist():
    if(request.cookies.get('usera')):
        session = cassandra_connect()
        session.execute('USE "icecream"')
        orders = session.execute(
            """SELECT invoice_no, amount, c_id, date, p_id, quantity,time,p_name FROM orders """)
        return render_template('order_list.html', orders=orders)
    else:
        return render_template("login.html", message="Unauthorized Action.", status=-1)


@app.route('/userlist', methods=['GET', 'POST'])
def userlist():
    if(request.cookies.get('usera')):
        if(request.method == "GET"):
            session = cassandra_connect()
            session.execute('USE "icecream"')
            users = session.execute(
                """SELECT email, address, mobile, name, user_type FROM users""")
            return render_template('user_list.html', users=users)
        if(request.method == "POST"):
            action = int(request.form['auth'])
            email = request.form['userd']
            if(action == 100):
                session = cassandra_connect()
                session.execute('USE "icecream"')
                session.execute(
                    """
                UPDATE users SET user_type=%(type)s WHERE email = %(email)s
                """, {'type': 'admin', 'email': email})
                users = session.execute(
                    """SELECT email, address, mobile, name, user_type FROM users""")
                return render_template('user_list.html', users=users, status=1, message="User is now Authorized as Admin.")
            if(action == 300):
                session = cassandra_connect()
                session.execute('USE "icecream"')
                session.execute(
                    """
                UPDATE users SET user_type=%(type)s WHERE email = %(email)s
                """, {'type': 'customer', 'email': email})
                users = session.execute(
                    """SELECT email, address, mobile, name, user_type FROM users""")
                return render_template('user_list.html', users=users, status=1, message="User is now Unauthorized but became an customer.")
    else:
        return render_template("login.html", message="Unauthorized Action.", status=-1)


@app.route('/update/id=<id>', methods=['GET', 'POST'])
def update(id):
    if(request.cookies.get('usera')):
        if(request.method == "GET"):
            iid = int(id)
            session = cassandra_connect()
            session.execute('USE "icecream"')
            rows = session.execute(
                """
                SELECT prod_id, prod_name, prod_type, quantity, man_date, exp_date, batch_no, rate,img_name FROM product where prod_id = %(id)s
            """, {'id': iid})
            return render_template('update.html', op=rows)
        if(request.method == "POST"):
            id = int(request.form['id'])
            prod_name = request.form['prod_name']
            type = request.form['type']
            quantity = int(request.form['quantity'])
            manufacturing_date = request.form['man_date']
            expiry_date = request.form['exp_date']
            batch = request.form['batch']
            rate = int(request.form['rate'])
            f = request.files['file']
            f.save(os.path.join('static', secure_filename(f.filename)))

            if(id and prod_name and type and quantity and manufacturing_date and expiry_date and batch and rate and f.filename):
                session = cassandra_connect()
                session.execute('USE "icecream"')
                session.execute(
                    """
                UPDATE product SET prod_name=%(prod_name)s, prod_type=%(prod_type)s, quantity=%(quantity)s, man_date=%(man_date)s, exp_date=%(exp_date)s, batch_no=%(batch_no)s, rate=%(rate)s, img_name=%(img_name)s WHERE prod_id = %(proddid)s
                """, {'prod_name': prod_name, 'prod_type': type, 'quantity': quantity, 'man_date': manufacturing_date, 'exp_date': expiry_date, 'batch_no': batch, 'rate': rate, 'img_name': '/static/'+f.filename, 'proddid': id})
                rows = session.execute(
                    'SELECT prod_id, prod_name, prod_type, quantity, man_date, exp_date, batch_no, rate FROM product')
                return render_template('add.html', op=rows, message="Successfully Updated.", status=1)
            else:
                return render_template('add.html', message="Error", status=-1)
    else:
        return render_template("login.html", message="Unauthorized Action.", status=-1)


@app.route('/delete/id=<id>', methods=['GET', 'POST'])
def delete(id):
    if(request.cookies.get('usera')):
        session = cassandra_connect()
        session.execute('USE "icecream"')
        session.execute(
            """
        DELETE FROM product
        WHERE prod_id = %(id)s IF EXISTS
        """, {'id': int(id)})
        rows = session.execute(
            'SELECT prod_id, prod_name, prod_type, quantity, man_date, exp_date, batch_no, rate FROM product')
        return render_template('add.html', op=rows, message="Successfully Deleted.", status=1)
    else:
        return render_template("login.html", message="Unauthorized Action.", status=-1)


@app.route('/add_product', methods=['GET', 'POST'])
def add_ingredient():
    if(request.cookies.get('usera')):
        if request.method == "GET":
            session = cassandra_connect()
            session.execute('USE "icecream"')
            id = session.execute("""
            SELECT value FROM flag WHERE forname= %(inv)s
            """, {'inv': "prodid"})
            return render_template("add_product.html", prodid=id[0].value)
        if request.method == "POST":
            id = int(request.form['id'])
            prod_name = request.form['prod_name']
            type = request.form['type']
            quantity = int(request.form['quantity'])
            manufacturing_date = request.form['man_date']
            expiry_date = request.form['exp_date']
            batch = request.form['batch']
            rate = int(request.form['rate'])
            f = request.files['file']
            f.save(os.path.join('static', secure_filename(f.filename)))

            if(id and prod_name and type and quantity and manufacturing_date and expiry_date and batch and rate and f.filename):
                session = cassandra_connect()
                session.execute('USE "icecream"')
                session.execute(
                    """
                INSERT INTO product (prod_id, prod_name, prod_type, quantity, man_date, exp_date, batch_no, rate, img_name)  
                VALUES(%(prod_id)s,%(prod_name)s,%(prod_type)s,%(quantity)s,%(man_date)s,%(exp_date)s,%(batch_no)s,%(rate)s,%(img_name)s)
                """, {'prod_id': id, 'prod_name': prod_name, 'prod_type': type, 'quantity': quantity, 'man_date': manufacturing_date, 'exp_date': expiry_date, 'batch_no': batch, 'rate': rate, 'img_name': '/static/'+f.filename})
                session.execute(
                    """
                UPDATE flag SET value = %(val)s WHERE forname = %(forname)s
                """, {'val': int(id)+1, 'forname': "prodid"})
                return render_template("add_product.html", message="Successfully Inserted.", status=1)
            else:
                return render_template("add_product.html", message="All fields are compulsory.", status=-1)
    else:
        return render_template("login.html", message="Unauthorized Action.", status=-1)


@app.route('/stock', methods=['GET', 'POST'])
def add():
    if(request.cookies.get('usera')):
        session = cassandra_connect()
        session.execute('USE "icecream"')
        rows = session.execute(
            'SELECT prod_id, prod_name, prod_type, quantity, man_date, exp_date, batch_no, rate FROM product')
        return render_template('add.html', op=rows)
    else:
        return render_template("login.html", message="Unauthorized Action.", status=-1)


if __name__ == "__main__":
    app.run(debug=True)
