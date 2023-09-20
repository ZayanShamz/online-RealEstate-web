from flask import *
import pymysql
from geopy.geocoders import Nominatim
import os

app = Flask(__name__)
app.secret_key = "classified"


con = pymysql.connect(host='localhost', port=3306, user='root', password='1234', db='realestate')
cmd = con.cursor()


geoLocator = Nominatim(user_agent="geoapiExercises")


@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        # location part
        lati = request.form['lati']
        longi = request.form['longi']
        session['lati'] = lati
        session['longi'] = longi

        username = request.form['email']
        password = request.form['passwd']
        cmd.execute("SELECT * FROM login WHERE username='"+username+"' AND password='"+password+"'")
        account = cmd.fetchone()

        if account:
            usertype = account[3]
            session['usertype'] = account[3]
            session['lid'] = account[0]
            if usertype == 'admin':
                return redirect(url_for('adminHome'))
            elif usertype == 'user':
                return redirect(url_for('userHome'))
        else:
            return "<script>alert('invalid username or password');window.location='/'</script>"
    else:
        return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['dealerName']
        email = request.form['dealerEmail']
        phone = request.form['dealerPhone']
        gen = request.form['gender']
        dob = request.form['dealerDob']
        passwd = request.form['dealerPassword']

        cmd.execute("INSERT INTO login values(NULL, '"+email+"', '"+passwd+"', 'user')")
        lid = str(con.insert_id())
        cmd.execute("INSERT INTO `dealer` VALUES(NULL,'"+lid+"','"+name+"','"+email+"','"+phone+"','"+gen+"','"+dob+"', '"+passwd+"')")
        con.commit()

        return "<script>alert('Registration Successful');window.location='/'</script>"
    else:
        return render_template('signup.html')


@app.route('/adminHome')
def adminHome():
    return render_template("adminhome.html")


# ------------------------------------- ADMIN - DEALER - FUNCTIONS -----------------------------------------------------
@app.route('/addDealer', methods=['GET', 'POST'])
def addDealer():
    if request.method == 'POST':
        name = request.form['dealerName']
        email = request.form['dealerEmail']
        phone = request.form['dealerPhone']
        gender = request.form['gender']
        dob = request.form['dealerDob']
        password = request.form['dealerPassword']

        cmd.execute("insert into `login` values(NULL, '"+email+"', '"+password+"', 'user')")
        lid = con.insert_id()
        cmd.execute("INSERT INTO `dealer` VALUES(NULL,'"+str(lid)+"', '"+name+"', '"+email+"', '"+phone+"','"+gender+"', '"+dob+"', '"+password+"')")
        con.commit()
        return redirect(url_for('adminHome'))
    else:
        cmd.execute("SELECT * FROM `dealer`")
        res = cmd.fetchall()
        return render_template('admin-add-dealer.html', dealers=res)


@app.route('/viewDealerList', methods=['GET', 'POST'])
def viewDealerList():
    if request.method == 'POST':
        dname = request.form['dname']
        cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `dealer` \
        WHERE `name` LIKE '%{dname}%' ")
        res = cmd.fetchall()
        return render_template('admin-view-dealerList.html', dealers=res)
    else:
        cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `dealer`")
        res = cmd.fetchall()
        return render_template('admin-view-dealerList.html', dealers=res)


@app.route('/viewDealer/<lid>')
def viewDealer(lid):

    cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)),'%Y') + 0 AS age FROM `dealer` WHERE `login_id`='"+lid+"'")
    res = cmd.fetchone()

    cmd.execute("SELECT `plot_id`,`plot`.`name`,`address`,`dealer`.`name` FROM `dealer`, `plot` WHERE \
    `plot`.`login_id`=`dealer`.`login_id` AND `plot`.`login_id`='"+lid+"' ")
    plots = cmd.fetchall()

    cmd.execute("SELECT `rental_id`,`rental`.`name`,`address`,`dealer`.`name` FROM `dealer`, `rental` \
    WHERE `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`login_id`='"+lid+"'")
    rentals = cmd.fetchall()

    return render_template('admin-view-dealer.html', dealer=res, plots=plots, rentals=rentals)


@app.route('/removeDealer/<lid>')
def removeDealer(lid):

    aid = session['lid']
    cmd.execute("SELECT `plot_id` FROM `plot` WHERE `login_id`='"+lid+"'")
    pids = [i[0] for i in cmd.fetchall()]
    if pids:
        pids.append(0)
        pids = tuple(pids)
    else:
        pids = (0, 0)
    cmd.execute(f"SELECT `filename` FROM `plot_images` WHERE `ref_id` IN {pids}")
    res = [i[0] for i in cmd.fetchall()]
    for i in res:
        os.remove("static/images/plot/" + i)

    cmd.execute(f"DELETE FROM `plot_images` WHERE `ref_id` IN {pids}")
    cmd.execute(f"DELETE FROM `plot_locations` WHERE `ref_id` IN {pids}")
    cmd.execute(f"DELETE FROM `plot_requests` WHERE `pid` IN {pids}")

    cmd.execute("SELECT `rental_id` FROM `rental` WHERE `login_id`='"+lid+"'")
    rids = [i[0] for i in cmd.fetchall()]
    if rids:
        rids.append(0)
        rids = tuple(rids)
    else:
        rids = (0, 0)
    cmd.execute(f"SELECT `filename` FROM `rental_images` WHERE `ref_id` IN {rids}")
    res1 = [i[0] for i in cmd.fetchall()]
    for i in res1:
        os.remove("static/images/rentals/" + i)

    cmd.execute(f"DELETE FROM `rental_images` WHERE `ref_id` IN {rids}")
    cmd.execute(f"DELETE FROM `rental_locations` WHERE `ref_id` IN {rids}")
    cmd.execute(f"DELETE FROM `rental_requests` WHERE `rid` IN {rids}")

    cmd.execute("DELETE FROM `dealer` WHERE `login_id`='"+lid+"'")
    cmd.execute("DELETE FROM `plot` WHERE `login_id`='"+lid+"'")
    cmd.execute("DELETE FROM `rental` WHERE `login_id`='"+lid+"'")
    cmd.execute("DELETE FROM `login` WHERE `lid`='"+lid+"'")
    con.commit()

    if aid == 1:
        return redirect(request.referrer)
    else:
        return f"<script>alert('Profile Deleted');window.location='/'</script>"


@app.route('/editDealer/<lid>', methods=['GET', 'POST'])
def editDealer(lid):
    cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `dealer` WHERE `login_id`='"+lid+"' ")
    res = cmd.fetchone()

    if request.method == 'POST':
        name = request.form['dealerName']
        email = request.form['dealerEmail']
        phone = request.form['dealerPhone']
        gender = request.form['gender']
        dob = request.form['dealerDob']

        cmd.execute("UPDATE `dealer` SET `name`='"+name+"', `email`='"+email+"', `phone`='"+phone+"', \
        `gender`='"+gender+"', `dob`='"+dob+"' WHERE `login_id`='"+lid+"'")
        con.commit()
        return f"<script>alert('Updated');window.location='/viewDealer/{lid}'</script>"
    else:
        return render_template('admin-edit-dealer.html', dealer=res)


# ------------------------------------- ADMIN - PLOT - FUNCTIONS -----------------------------------------------------
@app.route('/addPlot',methods=["GET","POST"])
def addPlot():
    global geoLocator
    cmd.execute("SELECT `login_id`,`name` FROM `dealer`")
    res = cmd.fetchall()
    if request.method == 'POST':
        name = request.form['pname']
        dealer_id = request.form['dealer']
        area = request.form['area']
        plot_type = request.form['ptype']
        price = request.form['price']

        lati = request.form['lat']
        long = request.form['lon']
        loc = geoLocator.reverse(lati + "," + long)
        address = loc.raw['address']

        state = address.get('state', '')
        county = address.get('county', '')
        zipcode = address.get('postcode', '')

        pfiles = request.files.getlist('files')
        count = len(pfiles)

        cmd.execute("SELECT `name` FROM `dealer` WHERE `dealer_id`='"+dealer_id+"'")
        usr = cmd.fetchone()[0]

        cmd.execute("INSERT INTO `plot` VALUES(NULL,'"+dealer_id+"', '"+name+"','"+loc+"', '"+area+"', '"+plot_type+"', '"+price+"',null, null, '"+str(count)+"', 'pending', '0')")
        pid = str(con.insert_id())

        cmd.execute("INSERT INTO `plot_locations` VALUES(NULL,'"+pid+"','"+lati+"','"+long+"', '"+loc+"', '"+state+"', '"+county+"', '"+str(zipcode)+"')")
        con.commit()

        c = 1
        for file in pfiles:
            # photo file save to folder
            split = str.split(file.filename, '.')
            ext = '.' + split[len(split) - 1]
            fname = usr + f"({dealer_id})_" + name
            photo = fname + "-" + str(c) + ext
            file.save('static/images/plot/' + photo)

            cmd.execute("INSERT INTO `plot_images` VALUES(NULL, '"+pid+"', '"+photo+"')")
            cmd.execute("UPDATE `plot` SET `filename`='"+fname+"', `ext`='"+ext+"' WHERE `plot_id`='"+pid+"' ")
            con.commit()
            c += 1
        return "<script>alert('Plot Added Successfully');window.location='adminHome'</script>"
    else:
        return render_template("admin-add-plot.html", dealer=res)


@app.route('/viewPlotList', methods=['GET', 'POST'])
def viewPlotList():
    if request.method == 'POST':
        pname = request.form['dname']
        cmd.execute(f"SELECT `plot`.*, `plot_locations`.`address`,`state`,`county`, `dealer`.`name`,`dealer`.`login_id` \
        FROM `dealer`, `plot_locations`, `plot` WHERE `plot`.`plot_id`=`plot_locations`.`ref_id` \
        AND `plot`.`login_id`=`dealer`.`login_id` AND (`plot`.`name` LIKE '%{pname}%' OR `dealer`.`name` LIKE '%{pname}%')")
        res = cmd.fetchall()
        return render_template('admin-view-plotList.html', plots=res)
    else:
        cmd.execute("SELECT `plot`.*, `plot_locations`.`address`,`state`,`county`, `dealer`.`name`,`dealer`.`login_id` FROM \
        `dealer`, `plot_locations`, `plot` WHERE `plot`.`plot_id`=`plot_locations`.`ref_id` AND `plot`.`login_id`=`dealer`.`login_id`")
        res = cmd.fetchall()
        return render_template('admin-view-plotList.html', plots=res)


@app.route('/deletePlot/<pid>')
def deletePlot(pid):
    cmd.execute("SELECT `filename` FROM `plot_images` WHERE `ref_id`='"+pid+"'")
    res = [i[0] for i in cmd.fetchall()]
    for i in res:
        os.remove("static/images/plot/" + i)
    cmd.execute("DELETE FROM `plot` WHERE `plot_id`='"+pid+"' ")
    cmd.execute("DELETE FROM `plot_locations` WHERE `ref_id`='"+pid+"' ")
    cmd.execute("DELETE FROM `plot_images` WHERE `ref_id`='"+pid+"' ")
    con.commit()
    return redirect(request.referrer)


@app.route('/viewPlot/<pid>')
def viewPlot(pid):
    cmd.execute("SELECT `plot`.*, `plot_locations`.`address`,`state`,`county`, `dealer`.`login_id`, `dealer`.`name`,`email`\
    FROM `dealer`, `plot_locations`, `plot` WHERE `plot`.`plot_id`=`plot_locations`.`ref_id` \
    AND `plot`.`login_id`=`dealer`.`login_id` AND `plot`.`plot_id`='"+pid+"' ")
    res = cmd.fetchone()

    cmd.execute("SELECT `latitude`,`longitude` FROM `plot_locations` WHERE `ref_id`='"+pid+"' ")
    lat, lon = cmd.fetchone()
    return render_template('admin-view-plot.html', plot=res, lat=lat, lon=lon)


@app.route('/editPlot/<pid>', methods=['GET', 'POST'])
def editPlot(pid):
    cmd.execute("SELECT `login_id`,`name` FROM `dealer`")
    res = cmd.fetchall()

    cmd.execute("SELECT `plot`.*,`dealer`.`login_id`, `dealer`.`name` \
    FROM `dealer`, `plot_locations`, `plot` WHERE `plot`.`plot_id`=`plot_locations`.`ref_id` \
    AND `plot`.`login_id`=`dealer`.`login_id` AND `plot`.`plot_id`='"+pid+"' ")
    result = cmd.fetchone()

    ogc = result[9]
    fname = result[7]
    ext = result[8]

    if request.method == 'POST':
        name = request.form['pname']
        dealer_id = request.form['dealer']
        area = request.form['area']
        plot_type = request.form['ptype']
        price = request.form['price']

        lati = request.form['lat']
        long = request.form['lon']

        if lati or long:
            loc = geoLocator.reverse(lati + "," + long)
            address = loc.raw['address']

            state = address.get('state', '')
            county = address.get('county', '')
            zipcode = address.get('postcode', '')

            cmd.execute("UPDATE `plot` SET `address`='"+str(loc)+"' WHERE `plot_id`='"+pid+"' ")
            cmd.execute("UPDATE `plot_locations` SET `latitude`='"+lati+"', `longitude`='"+long+"', `address`='"+str(loc)+"', \
            `state`='"+state+"', `county`='"+county+"', `zipcode`='"+str(zipcode)+"' WHERE `ref_id`='"+pid+"' ")
            con.commit()

        pfiles = request.files.getlist('files')
        if pfiles:
            for file in pfiles:
                ogc = int(ogc) + 1
                photo = fname + "-" + str(ogc) + ext
                file.save('static/images/plot/' + photo)

                cmd.execute("INSERT INTO `plot_images` VALUES(NULL, '"+pid+"', '"+photo+"')")
                con.commit()

            cmd.execute("UPDATE `plot` SET `count`='"+str(ogc)+"' WHERE `plot_id`='"+pid+"' ")
            con.commit()
        cmd.execute("UPDATE `plot` SET `login_id`='"+dealer_id+"', `name`='"+name+"',`area`='"+area+"',\
        `type`='"+plot_type+"',`price`='"+price+"' WHERE `plot_id`='"+pid+"' ")
        con.commit()
        return f"<script>alert('Updated');window.location='/viewPlot/{pid}'</script>"

    else:
        return render_template('admin-edit-plot.html', plot=result, dealer=res)


# ------------------------------------- ADMIN - RENTAL - FUNCTIONS -----------------------------------------------------

@app.route('/addRental',methods=["GET","POST"])
def addRental():
    global geoLocator
    cmd.execute("SELECT `login_id`,`name` FROM `dealer`")
    res = cmd.fetchall()
    if request.method == 'POST':
        name = request.form['rname']
        dealer_id = request.form['dealer']
        area = request.form['area']
        storey = request.form['storey']
        rent = request.form['rent']

        lati = request.form['lat']
        long = request.form['lon']
        loc = geoLocator.reverse(lati + "," + long)
        address = loc.raw['address']

        state = address.get('state', '')
        county = address.get('county', '')
        zipcode = address.get('postcode', '')

        pfiles = request.files.getlist('files')
        count = len(pfiles)

        cmd.execute("SELECT `name` FROM `dealer` WHERE `login_id`='"+dealer_id+"'")
        usr = cmd.fetchone()[0]

        cmd.execute("INSERT INTO `rental` VALUES(NULL,'"+dealer_id+"','"+name+"','"+str(loc)+"','"+area+"','"+rent+"','"+storey+"',NULL,NULL, '"+str(count)+"','pending','0')")
        rid = str(con.insert_id())

        cmd.execute("INSERT INTO `rental_locations` VALUES(NULL,'"+rid+"','"+lati+"','"+long+"', '"+str(loc)+"', '"+state+"', '"+county+"', '"+str(zipcode)+"')")
        con.commit()

        c = 1
        for file in pfiles:
            split = str.split(file.filename, '.')
            ext = '.' + split[len(split) - 1]
            fname = usr + f"({dealer_id})_" + name
            photo = fname + "-" + str(c) + ext
            file.save('static/images/rentals/' + photo)

            cmd.execute("INSERT INTO `rental_images` VALUES(NULL, '"+rid+"', '"+photo+"')")
            cmd.execute("UPDATE `rental` SET `filename`='"+fname+"', `ext`='"+ext+"' WHERE `rental_id`='"+rid+"' ")
            con.commit()
            c += 1
        return "<script>alert('Rental Added Successfully');window.location='adminHome'</script>"
    else:
        return render_template("admin-add-rental.html", dealer=res)


@app.route('/viewRentalList')
def viewRentalList():
    cmd.execute("SELECT `rental`.*, `rental_locations`.`address`,`state`,`county`, `dealer`.`name`,`dealer`.`login_id` \
    FROM `dealer`, `rental_locations`, `rental` WHERE `rental`.`rental_id`=`rental_locations`.`ref_id` \
    AND `rental`.`login_id`=`dealer`.`login_id` ")
    res = cmd.fetchall()
    return render_template('admin-view-rentalList.html', rentals=res)


@app.route('/viewRental/<rid>')
def viewRental(rid):
    cmd.execute("SELECT `rental`.*, `rental_locations`.`address`,`state`,`county`, `dealer`.`login_id`, `dealer`.`name`,`email` \
    FROM `dealer`, `rental_locations`, `rental`  WHERE `rental`.`rental_id`=`rental_locations`.`ref_id` \
    AND `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`rental_id`='"+rid+"' ")
    res = cmd.fetchone()

    cmd.execute("SELECT `latitude`,`longitude` FROM `rental_locations` WHERE `ref_id`='"+rid+"' ")
    lat, lon = cmd.fetchone()
    return render_template('admin-view-rental.html', rental=res, lat=lat, lon=lon)


@app.route('/deleteRental/<rid>')
def deleteRental(rid):
    cmd.execute("SELECT `filename` FROM `rental_images` WHERE `ref_id`='"+rid+"'")
    res1 = [i[0] for i in cmd.fetchall()]
    for i in res1:
        os.remove("static/images/rentals/" + i)
    cmd.execute("DELETE FROM `rental` WHERE `rental_id`='"+rid+"' ")
    cmd.execute("DELETE FROM `rental_locations` WHERE `ref_id`='"+rid+"' ")
    cmd.execute("DELETE FROM `rental_images` WHERE `ref_id`='"+rid+"' ")
    con.commit()
    return redirect(request.referrer)


@app.route('/editRental/<rid>', methods=['POST', 'GET'])
def editRental(rid):
    cmd.execute("SELECT `login_id`,`name` FROM `dealer`")
    result = cmd.fetchall()

    cmd.execute("SELECT `rental`.*, `rental_locations`.`address`,`dealer`.`login_id`, `dealer`.`name` \
    FROM `dealer`, `rental_locations`, `rental`  WHERE `rental`.`rental_id`=`rental_locations`.`ref_id` \
    AND `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`rental_id`='"+rid+"' ")
    res = cmd.fetchone()

    fname = res[7]
    ext = res[8]
    ogc = res[9]

    if request.method == 'POST':
        name = request.form['rname']
        dealer_id = request.form['dealer']
        area = request.form['area']
        storey = request.form['storey']
        rent = request.form['rent']

        lati = request.form['lat']
        long = request.form['lon']

        if lati or long:
            loc = geoLocator.reverse(lati + "," + long)
            address = loc.raw['address']

            state = address.get('state', '')
            county = address.get('county', '')
            zipcode = address.get('postcode', '')

            cmd.execute("UPDATE `rental` SET `address`='"+str(loc)+"' WHERE `plot_id`='"+rid+"' ")
            cmd.execute("UPDATE `rental_locations` SET `latitude`='"+lati+"', `longitude`='"+long+"', `address`='"+str(loc)+"', \
            `state`='"+state+"', `county`='"+county+"', `zipcode`='"+str(zipcode)+"' WHERE `ref_id`='"+rid+"' ")
            con.commit()

        pfiles = request.files.getlist('files')
        if pfiles:

            for f in pfiles:
                ogc = int(ogc) + 1
                photo = fname + "-" + str(ogc) + ext
                f.save('static/images/rentals/' + photo)

                cmd.execute("INSERT INTO `plot_images` VALUES(NULL, '"+rid+"', '"+photo+"')")
                con.commit()

            cmd.execute("UPDATE `rental` SET `count`='"+str(ogc)+"' WHERE `rental_id`='"+rid+"' ")
            con.commit()
        cmd.execute("UPDATE `rental` SET `login_id`='"+dealer_id+"', `name`='"+name+"',`area`='"+area + "',\
        `storey`='"+storey+"',`rent`='"+rent+"' WHERE `rental_id`='"+rid+"' ")
        con.commit()
        return f"<script>alert('Updated');window.location='/viewRental/{rid}'</script>"
    else:
        return render_template('admin-edit-rental.html', rental=res, dealer=result)


# ------------------------------------- ADMIN - Engineer - FUNCTIONS -----------------------------------------------------


@app.route('/addEngineer', methods=['GET', 'POST'])
def addEngineer():
    global geoLocator
    if request.method == 'POST':
        name = request.form['ename']
        exp = request.form['exp']
        email = request.form['email']
        phone = request.form['phone']
        gender = request.form['gender']
        discipline = request.form['disc']
        dob = request.form['dob']

        lati = request.form['lat']
        long = request.form['lon']
        loc = geoLocator.reverse(lati + "," + long)

        file = request.files['files']
        ext = str.split(file.filename, '.')[-1]

        photo = name + '.' + ext
        file.save('static/images/engineers/' + photo)

        cmd.execute("INSERT INTO `engineer` VALUES(NULL,'"+name+"','"+exp+"','"+discipline+"','"+email+"','"+phone+"',\
        '"+gender+"','"+dob+"','"+str(loc)+"','"+photo+"' )")
        con.commit()

        return "<script>alert('Engineer Added Successfully');window.location='adminHome'</script>"
    else:
        return render_template('admin-add-engineer.html')


@app.route('/viewEngineers', methods=['GET', 'POST'])
def viewEngineers():
    if request.method == "POST":
        kword = request.form['kword']
        cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `engineer`\
         WHERE `name` LIKE '%{kword}%' OR `discipline` LIKE '%{kword}%'")
        res = cmd.fetchall()
        print(res)
    else:
        cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `engineer`")
        res = cmd.fetchall()
        print(res)
    return render_template('admin-view-engList.html', res=res)


@app.route('/viewEngineer/<eid>')
def viewEngineer(eid):
    cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `engineer` WHERE `eng_id`='"+eid+"' ")
    res = cmd.fetchone()
    return render_template('admin-view-eng.html', eng=res)


@app.route('/editEngineer/<eid>', methods=['GET', 'POST'])
def editEngineer(eid):
    if request.method == 'POST':
        name = request.form['ename']
        gender = request.form['gender']
        dob = request.form['dob']
        phone = request.form['phone']
        email = request.form['email']
        discipline = request.form['disc']
        exp = request.form['exp']

        loc = request.form['loc']
        fname = request.form['fname']

        lati = request.form['lat']
        long = request.form['lon']
        if lati and long:
            loc = geoLocator.reverse(lati + "," + long)

        file = request.files['files']
        if file:
            os.remove('static/images/engineers/' + fname)

            ext = str.split(file.filename, '.')[-1]
            fname = name + '.' + ext
            file.save('static/images/engineers/' + fname)

        cmd.execute("UPDATE `engineer` SET `name`='"+name+"', `exp`='"+exp+"', `discipline`='"+discipline+"',\
        `email`='"+email+"', `phone`='"+phone+"', `gender`='"+gender+"', `dob`='"+dob+"', `place`='"+str(loc)+"',\
        `filename`='"+fname+"' WHERE `eng_id`='"+eid+"'")
        con.commit()

        return redirect(f"/viewEngineer/{eid}")

    else:
        cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `engineer` WHERE `eng_id`='"+eid+"'")
        res = cmd.fetchone()
        print(res)
        return render_template('admin-edit-eng.html', eng=res)


@app.route('/deleteEngineer/<eid>')
def deleteEngineer(eid):
    cmd.execute("SELECT `filename` FROM `engineer` WHERE `eng_id`='"+eid+"'")
    res = cmd.fetchone()[0]
    if res:
        os.remove("static/images/engineers/" + res)
    cmd.execute("DELETE FROM `engineer` WHERE `eng_id`='"+eid+"' ")
    con.commit()
    return redirect(url_for('viewEngineers'))


# ------------------------------------- ADMIN - MERCHANT - FUNCTIONS -----------------------------------------------------


@app.route('/addMerchant', methods=['GET', 'POST'])
def addMerchant():
    global geoLocator
    if request.method == 'POST':
        name = request.form['mname']
        dob = request.form['dob']
        email = request.form['email']
        phone = request.form['phone']
        bname = request.form['bname']
        btype = request.form['btype']

        lati = request.form['lat']
        long = request.form['lon']
        loc = geoLocator.reverse(lati + "," + long)

        file = request.files['files']
        ext = str.split(file.filename, '.')[-1]

        photo = name + '.' + ext
        file.save('static/images/merchant/' + photo)

        cmd.execute("INSERT INTO `merchant` VALUES(NULL,'"+name+"','"+dob+"','"+email+"','"+phone+"',\
        '"+bname+"','"+btype+"','"+str(loc)+"','"+photo+"' )")
        con.commit()

        return "<script>alert('Merchant Added Successfully');window.location='adminHome'</script>"
    else:
        return render_template('admin-add-merch.html')


@app.route('/viewMerchants', methods=['GET', 'POST'])
def viewMerchants():
    if request.method == "POST":
        kword = request.form['kword']
        cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `merchant`\
        WHERE `name` LIKE '%{kword}%' OR `bname` LIKE  '%{kword}%' OR `btype` LIKE  '%{kword}%'")
        res = cmd.fetchall()
        print(res)
        return render_template('admin-view-merchList.html', res=res)
    else:
        cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `merchant`")
        res = cmd.fetchall()
        print(res)
        return render_template('admin-view-merchList.html', res=res)


@app.route('/viewMerchant/<mid>')
def viewMerchant(mid):
    cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `merchant` WHERE `merc_id`='"+mid+"'")
    res = cmd.fetchone()
    return render_template('admin-view-merch.html', merch=res)


@app.route('/deleteMerchant/<mid>')
def deleteMerchant(mid):
    cmd.execute("SELECT `filename` FROM `merchant` WHERE `merc_id`='"+mid+"'")
    res = cmd.fetchone()[0]
    if res:
        os.remove("static/images/merchant/" + res)
    cmd.execute("DELETE FROM `merchant` WHERE `merc_id`='"+mid+"' ")
    con.commit()
    return redirect(url_for('viewMerchants'))


@app.route('/editMerchant/<mid>', methods=['GET', 'POST'])
def editMerchant(mid):
    if request.method == 'POST':
        name = request.form['ename']
        dob = request.form['dob']
        email = request.form['email']
        phone = request.form['phone']
        bname = request.form['bname']
        btype = request.form['btype']

        loc = request.form['loc']
        fname = request.form['fname']

        lati = request.form['lat']
        long = request.form['lon']
        if lati and long:
            loc = geoLocator.reverse(lati + "," + long)

        file = request.files['files']
        if file:
            os.remove('static/images/merchant/' + fname)

            ext = str.split(file.filename, '.')[-1]
            fname = name + '.' + ext
            file.save('static/images/merchant/' + fname)

        cmd.execute("UPDATE `merchant` SET `name`='"+name+"', `dob`='"+dob+"', `email`='"+email+"', `phone`='"+phone+"',\
        `bname`='"+bname+"', `btype`='"+btype+"', `location`='"+str(loc)+"', `filename`='"+fname+"' WHERE `merc_id`='"+mid+"'")
        con.commit()

        return redirect(f"/viewMerchant/{mid}")

    else:
        cmd.execute("SELECT * FROM `merchant` WHERE `merc_id`='"+mid+"'")
        res = cmd.fetchone()
        print(res)
        return render_template('admin-edit-merch.html', merch=res)


# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------- user ---------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


@app.route('/userHome')
def userHome():
    lid = session['lid']
    if request.method == 'POST':
        pass
    else:
        cmd.execute("SELECT * FROM `plot` WHERE `login_id`='"+str(lid)+"' ")
        res = cmd.fetchall()
        return render_template("userhome.html", res=res)


@app.route('/userProfile')
def userProfile():
    lid = session['lid']
    lid = str(lid)

    cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)),'%Y') + 0 AS age FROM `dealer` WHERE `login_id`='"+lid+"'")
    res = cmd.fetchone()

    cmd.execute("SELECT `plot_id`,`plot`.`name`,`address`,`dealer`.`name` FROM `dealer`, `plot` WHERE \
    `plot`.`login_id`=`dealer`.`login_id` AND `plot`.`login_id`='"+lid+"' ")
    plots = cmd.fetchall()

    cmd.execute("SELECT `rental_id`,`rental`.`name`,`address`,`dealer`.`name` FROM `dealer`, `rental` \
    WHERE `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`login_id`='"+lid+"'")
    rentals = cmd.fetchall()

    return render_template('user-profile.html', dealer=res, plots=plots, rentals=rentals)


@app.route('/userAddPlot', methods=['POST', 'GET'])
def userAddPlot():
    lid = session['lid']
    if request.method == 'POST':
        name = request.form['pname']
        area = request.form['area']
        plot_type = request.form['ptype']
        price = request.form['price']

        lati = request.form['lat']
        long = request.form['lon']
        loc = geoLocator.reverse(lati + "," + long)

        address = loc.raw['address']
        state = address.get('state', '')
        county = address.get('county', '')
        zipcode = address.get('postcode', '')

        pfiles = request.files.getlist('files')
        count = len(pfiles)

        cmd.execute("SELECT `name` FROM `dealer` WHERE `login_id`='"+str(lid)+"' ")
        usr = cmd.fetchone()[0]

        cmd.execute("INSERT INTO `plot` VALUES(NULL, '"+str(lid)+"', '"+name+"', '"+str(loc)+"', '"+area+"', \
        '"+plot_type+"', '"+price+"',null, null, '"+str(count)+"', 'pending', '0')")
        pid = str(con.insert_id())

        cmd.execute("INSERT INTO `plot_locations` VALUES(NULL, '"+pid+"', '"+lati+"', '"+long+"', '"+str(loc)+"', \
        '"+state+"', '"+county+"', '"+str(zipcode)+"')")
        con.commit()

        c = 1
        for file in pfiles:
            # photo file save to folder
            split = str.split(file.filename, '.')
            ext = '.' + split[len(split) - 1]
            fname = usr + f"({lid})_" + name
            photo = fname + "-" + str(c) + ext
            file.save('static/images/plot/' + photo)

            cmd.execute("INSERT INTO `plot_images` VALUES(NULL, '"+pid+"', '"+photo+"')")
            cmd.execute("UPDATE `plot` SET `filename`='"+fname+"', `ext`='"+ext+"' WHERE `plot_id`='"+pid+"' ")
            con.commit()
            c += 1
        return "<script>alert('Plot Added Successfully');window.location='/userHome'</script>"
    else:
        return render_template('user-add-plot.html')


@app.route('/userPlots')
def userPlots():
    lid = str(session['lid'])
    cmd.execute("SELECT `plot`.*, `plot_locations`.`county`,`state` FROM `plot`, `plot_locations` \
    WHERE `plot_locations`.`ref_id`=`plot`.`plot_id` AND `plot`.`login_id`='"+lid+"' ORDER BY `name`")
    res = cmd.fetchall()
    return render_template('user-plots.html', plots=res)


@app.route('/userPlot/<pid>')
def userPlot(pid):
    # lid = str(session['lid'])
    cmd.execute("SELECT `plot`.*, `plot_locations`.`address`,`state`,`county`, `dealer`.`login_id`, `dealer`.`name`,`email`,`phone` \
    FROM `dealer`, `plot_locations`, `plot` WHERE `plot`.`plot_id`=`plot_locations`.`ref_id` \
    AND `plot`.`login_id`=`dealer`.`login_id` AND `plot`.`plot_id`='"+pid+"' ")
    res = cmd.fetchone()

    cmd.execute("SELECT `latitude`,`longitude` FROM `plot_locations` WHERE `ref_id`='"+pid+"' ")
    lat, lon = cmd.fetchone()

    cmd.execute("SELECT `dealer`.`login_id`,`name`, `plot_requests`.* FROM `plot_requests`,`dealer` \
    WHERE `plot_requests`.`dealer_id`=`dealer`.`login_id` AND `plot_requests`.`pid`='"+pid+"'")
    req = cmd.fetchall()

    return render_template('user-plot.html', plot=res, lat=lat, lon=lon, req=req)


@app.route('/userEditPlot/<pid>', methods=['GET','POST'])
def userEditPlot(pid):
    cmd.execute("SELECT `plot`.*,`dealer`.`login_id`, `dealer`.`name` \
    FROM `dealer`, `plot_locations`, `plot` WHERE `plot`.`plot_id`=`plot_locations`.`ref_id` \
    AND `plot`.`login_id`=`dealer`.`login_id` AND `plot`.`plot_id`='"+pid+"' ")
    result = cmd.fetchone()

    ogc = result[9]
    fname = result[7]
    ext = result[8]

    if request.method == 'POST':
        name = request.form['pname']
        area = request.form['area']
        plot_type = request.form['ptype']
        price = request.form['price']

        lati = request.form['lat']
        long = request.form['lon']

        if lati or long:
            loc = geoLocator.reverse(lati + "," + long)
            address = loc.raw['address']

            state = address.get('state', '')
            county = address.get('county', '')
            zipcode = address.get('postcode', '')

            cmd.execute("UPDATE `plot` SET `address`='"+str(loc)+"' WHERE `plot_id`='"+pid+"' ")
            cmd.execute("UPDATE `plot_locations` SET `latitude`='"+lati+"', `longitude`='"+long+"', `address`='"+str(loc)+"', \
            `state`='"+state+"', `county`='"+county+"', `zipcode`='"+str(zipcode)+"' WHERE `ref_id`='"+pid+"' ")
            con.commit()

        pfiles = request.files['files']
        if pfiles:
            ogc = int(ogc) + 1
            photo = fname + "-" + str(ogc) + ext
            pfiles.save('static/images/plot/' + photo)

            cmd.execute("INSERT INTO `plot_images` VALUES(NULL, '"+pid+"', '"+photo+"')")
            con.commit()

            cmd.execute("UPDATE `plot` SET `count`='"+str(ogc)+"' WHERE `plot_id`='"+pid+"' ")
            con.commit()

        cmd.execute("UPDATE `plot` SET `name`='"+name+"',`area`='"+area+"',\
        `type`='"+plot_type+"',`price`='"+price+"' WHERE `plot_id`='"+pid+"' ")
        con.commit()
        return f"<script>alert('Updated');window.location='/userPlot/{pid}'</script>"

    else:
        return render_template('user-edit-plot.html', plot=result)


@app.route('/userViewBuyer/<bid>/<pid>/<loc>')
def userViewBuyer(bid,pid,loc):
    temp = "buy"
    cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `dealer` WHERE `login_id`='"+bid+"' ")
    res = cmd.fetchone()

    cmd.execute("SELECT `plot`.*, `plot_locations`.`address`,`state`,`county` FROM `dealer`, `plot_locations`, `plot` \
    WHERE `plot`.`plot_id`=`plot_locations`.`ref_id` \
    AND `plot`.`login_id`=`dealer`.`login_id` AND `plot`.`login_id`='"+bid+"' ")
    plots = cmd.fetchall()

    cmd.execute("SELECT `rental`.*, `rental_locations`.* FROM `dealer`, `rental_locations`, `rental` \
    WHERE `rental`.`rental_id`=`rental_locations`.`ref_id` \
    AND `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`login_id`='"+bid+"' ")
    rentals = cmd.fetchall()
    return render_template('user-view-buyer.html', buyer=res, plots=plots, rentals=rentals, pid=pid, temp=temp, loc=loc)


@app.route('/plotSearch', methods=['GET','POST'])
def plotSearch():
    temp = "srch"
    lid = str(session['lid'])
    if request.method == 'POST':
        sub = request.form['sub']

        # search by plot name
        if sub == 'srch':
            pname = request.form['pname']
            print(pname)
            if pname:
                cmd.execute(f"SELECT `plot`.*,`dealer`.`name`, `plot_locations`.`county`,`state` FROM \
                `plot`, `dealer`, `plot_locations` WHERE `plot`.`login_id`=`dealer`.`login_id` \
                AND `plot`.`plot_id`=`plot_locations`.`ref_id` AND `plot`.`name` LIKE '%{pname}%' OR `plot`.`address` LIKE '%{pname}%'")
                res = cmd.fetchall()
                print(res)
                if res:
                    return render_template("user-search-plots.html", plots=res, temp=temp)
                else:
                    return "<script>alert('No search result');window.location='/plotSearch'</script>"
            else:
                return "<script>alert('No search result');window.location='/plotSearch'</script>"

        # search by selection
        elif sub == 'srch2':
            ptype = request.form['type']
            price = request.form['price']
            area = request.form['area']

            cmd.execute(f"SELECT `plot`.*,`dealer`.`name`, `plot_locations`.`county`,`state` FROM \
            `plot`, `dealer`, `plot_locations` WHERE `plot_locations`.`ref_id`=`plot`.`plot_id` AND \
            `plot`.`login_id`=`dealer`.`login_id` AND `area` BETWEEN {area} AND price BETWEEN {price} AND `type`='{ptype}'")
            res = cmd.fetchall()
            print(res)

            if res:
                return render_template("user-search-plots.html", plots=res, temp=temp)
            else:
                return "<script>alert('No search result');window.location='/plotSearch'</script>"
    else:
        return render_template('user-search-prop.html')


@app.route('/user_viewPlot/<pid>/<t>')
def user_viewPlot(pid, t):
    lid = str(session['lid'])
    cmd.execute("SELECT `plot`.*, `plot_locations`.`address`,`state`,`county`, `dealer`.`login_id`, `dealer`.`name`,`email`,`phone` \
    FROM `dealer`, `plot_locations`, `plot` WHERE `plot`.`plot_id`=`plot_locations`.`ref_id` \
    AND `plot`.`login_id`=`dealer`.`login_id` AND `plot`.`plot_id`='"+pid+"' ")
    res = cmd.fetchone()

    cmd.execute("SELECT `latitude`,`longitude` FROM `plot_locations` WHERE `ref_id`='"+pid+"' ")
    lat, lon = cmd.fetchone()

    cmd.execute("SELECT * FROM `plot_requests` WHERE `pid`='"+pid+"' AND `dealer_id`='"+lid+"' ")
    dec = cmd.fetchall()

    return render_template('user-view-plot.html', plot=res, lat=lat, lon=lon, dec=dec, temp=t)


@app.route('/plotRequest/<pid>')
def plotRequest(pid):
    lid = str(session['lid'])
    cmd.execute("SELECT `requests` FROM `plot` WHERE `plot_id`='"+pid+"'")
    rqst = int(cmd.fetchone()[0])
    rqst += 1
    cmd.execute("UPDATE `plot` SET `requests`='"+str(rqst)+"' WHERE `plot_id`='"+pid+"' ")
    cmd.execute("INSERT INTO `plot_requests` VALUES(NULL, '"+pid+"', '"+lid+"', CURDATE(), CURTIME())")
    con.commit()
    return redirect(request.referrer)


@app.route('/plotWithdrawRequest/<pid>')
def plotWithdrawRequest(pid):
    lid = str(session['lid'])
    cmd.execute("SELECT `requests` FROM `plot` WHERE `plot_id`='"+pid+"'")
    rqst = int(cmd.fetchone()[0])
    rqst -= 1
    cmd.execute("UPDATE `plot` SET `requests`='"+str(rqst)+"' WHERE `plot_id`='"+pid+"' ")
    cmd.execute("DELETE FROM `plot_requests` WHERE `pid`='"+pid+"' AND `dealer_id`='"+lid+"'")
    con.commit()

    return redirect(request.referrer)


@app.route('/rentalSearch', methods=['GET','POST'])
def rentalSearch():
    lid = str(session['lid'])
    if request.method == 'POST':
        click = request.form['btnclick']
        if click == 'srch':
            rname = request.form['rname']
            if rname:
                print(rname)
                cmd.execute(f"SELECT `rental`.*,`dealer`.`name`, `rental_locations`.`county`,`state` FROM `rental`,`dealer`,\
                 `rental_locations` WHERE `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`rental_id`=`rental_locations`.`ref_id`\
                  AND `rental`.`name` LIKE '%{rname}%' OR `rental`.`address` LIKE '%{rname}%'")
                res = cmd.fetchall()
                print(res)
                if res:
                    print("hello")
                    return render_template("user-search-rentals.html", rentals=res)
                else:
                    return "<script>alert('No search result');window.location='/rentalSearch'</script>"
            else:
                print("NO RESULT")
                return "<script>alert('No search result');window.location='/rentalSearch'</script>"

        else:
            storey = request.form['storey']
            price = request.form['rprice']
            area = request.form['rarea']

            cmd.execute(f"SELECT `rental`.*,`dealer`.`name`, `rental_locations`.`county`,`state` FROM `rental`,`dealer`,\
             `rental_locations` WHERE `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`rental_id`=`rental_locations`.`ref_id` AND\
             `area` BETWEEN {area} AND `rent` BETWEEN {price} AND `storey`='{storey}' ")
            res = cmd.fetchall()

            if res:
                return render_template("user-search-rentals.html", rentals=res)
            else:
                return "<script>alert('No search result');window.location='/rentalSearch'</script>"
    else:
        return render_template('user-search-prop.html')


@app.route('/user_viewRental/<rid>/<t>')
def user_viewRental(rid, t):
    lid = str(session['lid'])
    cmd.execute("SELECT `rental`.*, `rental_locations`.`address`,`state`,`county`, `dealer`.`login_id`,`dealer`.`name`,\
    `email`,`phone` FROM `dealer`, `rental`, `rental_locations` WHERE `rental`.`login_id`=`dealer`.`login_id` AND \
    `rental`.`rental_id`=`rental_locations`.`ref_id` AND `rental`.`rental_id`='"+rid+"'")
    res = cmd.fetchone()

    cmd.execute("SELECT `latitude`,`longitude` FROM `rental_locations` WHERE `ref_id`='"+rid+"' ")
    lat, lon = cmd.fetchone()

    cmd.execute("SELECT * FROM `rental_requests` WHERE `rid`='"+rid+"' AND `dealer_id`='"+lid+"' ")
    dec = cmd.fetchall()

    return render_template('user-view-rental.html', rental=res, lat=lat, lon=lon, dec=dec, t=t)


@app.route('/rentalRequest/<rid>')
def rentalRequest(rid):
    lid = str(session['lid'])
    cmd.execute("SELECT `requests` FROM `rental` WHERE `rental_id`='"+rid+"'")
    rqst = int(cmd.fetchone()[0])
    rqst += 1
    cmd.execute("UPDATE `rental` SET `requests`='"+str(rqst)+"' WHERE `rental_id`='"+rid+"' ")
    cmd.execute("INSERT INTO `rental_requests` VALUES(NULL, '"+rid+"', '"+lid+"', CURDATE(), CURTIME())")
    con.commit()
    return redirect(request.referrer)


@app.route('/rentalWithdrawRequest/<rid>')
def rentalWithdrawRequest(rid):
    lid = str(session['lid'])
    cmd.execute("SELECT `requests` FROM `rental` WHERE `rental_id`='"+rid+"'")
    rqst = int(cmd.fetchone()[0])
    rqst -= 1
    cmd.execute("UPDATE `rental` SET `requests`='"+str(rqst)+"' WHERE `rental_id`='"+rid+"' ")
    cmd.execute("DELETE FROM `rental_requests` WHERE `rid`='"+rid+"' AND `dealer_id`='"+lid+"'")
    con.commit()

    return redirect(request.referrer)


@app.route('/userAddRental',methods=["GET","POST"])
def userAddRental():
    lid = str(session['lid'])
    global geoLocator
    if request.method == 'POST':
        name = request.form['rname']
        area = request.form['area']
        storey = request.form['storey']
        rent = request.form['rent']

        lati = request.form['lat']
        long = request.form['lon']
        loc = geoLocator.reverse(lati + "," + long)
        address = loc.raw['address']

        state = address.get('state', '')
        county = address.get('county', '')
        zipcode = address.get('postcode', '')

        pfiles = request.files.getlist('files')
        count = len(pfiles)

        cmd.execute("SELECT `name` FROM `dealer` WHERE `login_id`='"+lid+"'")
        usr = cmd.fetchone()[0]

        cmd.execute("INSERT INTO `rental` VALUES(NULL,'"+lid+"','"+name+"','"+str(loc)+"','"+area+"','"+rent+"','"+storey+"',NULL,NULL, '"+str(count)+"','pending','0')")
        rid = str(con.insert_id())

        cmd.execute("INSERT INTO `rental_locations` VALUES(NULL,'"+rid+"','"+lati+"','"+long+"', '"+str(loc)+"', '"+state+"', '"+county+"', '"+str(zipcode)+"')")
        con.commit()

        c = 1
        for file in pfiles:
            split = str.split(file.filename, '.')
            ext = '.' + split[len(split) - 1]
            fname = usr + f"({lid})_" + name
            photo = fname + "-" + str(c) + ext
            file.save('static/images/rentals/' + photo)

            cmd.execute("INSERT INTO `rental_images` VALUES(NULL, '"+rid+"', '"+photo+"')")
            cmd.execute("UPDATE `rental` SET `filename`='"+fname+"', `ext`='"+ext+"' WHERE `rental_id`='"+rid+"' ")
            con.commit()
            c += 1
        return "<script>alert('Rental Added Successfully');window.location='/userHome'</script>"
    else:
        return render_template("user-add-rental.html")


@app.route('/userRentals')
def userRentals():
    lid = str(session['lid'])
    cmd.execute("SELECT `rental`.*, `rental_locations`.`county`,`state` FROM `rental`,`rental_locations` \
    WHERE `rental_locations`.`ref_id`=`rental`.`rental_id` AND `rental`.`login_id`='"+lid+"' ORDER BY `name`")
    res = cmd.fetchall()
    return render_template('user-rentals.html', rental=res)


@app.route('/userRental/<rid>')
def userRental(rid):
    # lid = str(session['lid'])
    cmd.execute("SELECT `rental`.*, `rental_locations`.`address`,`state`,`county`, `dealer`.`login_id`, \
    `dealer`.`name`,`email`,`phone` FROM `dealer`, `rental_locations`, `rental` WHERE \
    `rental`.`rental_id`=`rental_locations`.`ref_id`AND `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`rental_id`='"+rid+"' ")
    res = cmd.fetchone()

    cmd.execute("SELECT `latitude`,`longitude` FROM `rental_locations` WHERE `ref_id`='"+rid+"' ")
    lat, lon = cmd.fetchone()

    cmd.execute("SELECT `dealer`.`login_id`,`name`, `rental_requests`.* FROM `rental_requests`,`dealer` \
    WHERE `rental_requests`.`dealer_id`=`dealer`.`login_id` AND `rental_requests`.`rid`='"+rid+"'")
    req = cmd.fetchall()

    return render_template('user-rentals.html', rental=res, lat=lat, lon=lon, req=req)


@app.route('/userEditRental/<rid>', methods=['POST', 'GET'])
def userEditRental(rid):

    cmd.execute("SELECT `rental`.*, `rental_locations`.`address`,`dealer`.`login_id`, `dealer`.`name` \
    FROM `dealer`, `rental_locations`, `rental`  WHERE `rental`.`rental_id`=`rental_locations`.`ref_id` \
    AND `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`rental_id`='"+rid+"' ")
    res = cmd.fetchone()

    ogc = res[9]
    fname = res[7]
    ext = res[8]

    if request.method == 'POST':
        name = request.form['rname']
        area = request.form['area']
        storey = request.form['storey']
        rent = request.form['rent']

        lati = request.form['lat']
        long = request.form['lon']

        if lati or long:
            loc = geoLocator.reverse(lati + "," + long)
            address = loc.raw['address']

            state = address.get('state', '')
            county = address.get('county', '')
            zipcode = address.get('postcode', '')

            cmd.execute("UPDATE `rental` SET `address`='"+str(loc)+"' WHERE `rental_id`='"+rid+"' ")
            cmd.execute("UPDATE `rental_locations` SET `latitude`='"+lati+"', `longitude`='"+long+"', `address`='"+str(loc)+"', \
            `state`='"+state+"', `county`='"+county+"', `zipcode`='"+str(zipcode)+"' WHERE `ref_id`='"+rid+"' ")
            con.commit()

        pfiles = request.files['files']
        if pfiles:
            ogc = int(ogc) + 1
            photo = fname + "-" + str(ogc) + ext
            pfiles.save('static/images/rentals/' + photo)

            cmd.execute("INSERT INTO `rental_images` VALUES(NULL, '"+rid+"', '"+photo+"')")
            con.commit()

            cmd.execute("UPDATE `rental` SET `count`='"+str(ogc)+"' WHERE `rental_id`='"+rid+"' ")
            con.commit()

        cmd.execute("UPDATE `rental` SET `name`='"+name+"',`area`='"+area + "',\
        `storey`='"+storey+"',`rent`='"+rent+"' WHERE `rental_id`='"+rid+"' ")
        con.commit()
        return f"<script>alert('Updated');window.location='/userRental/{rid}'</script>"
    else:
        return render_template('user-edit-rental.html', rental=res)


@app.route('/userSearchEng', methods=['GET','POST'])
def userSearchEng():
    if request.method == 'POST':
        sub = request.form['sub']
        res = None
        if sub == 'eng':
            ename = request.form['ename']
            cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `engineer` WHERE `name` LIKE '%{ename}%' ")
            res = cmd.fetchall()
        elif sub == 'place1':
            eplace = request.form['eplace']
            cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `engineer` WHERE `place` LIKE '%{eplace}%' ")
            res = cmd.fetchall()
        elif sub == 'Discipline':
            disc = request.form['disc']
            cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `engineer` WHERE `discipline` LIKE '%{disc}%' ")
            res = cmd.fetchall()
        return render_template('user-search-eng.html', res=res)
    else:
        return render_template('user-search-personnel.html')


@app.route('/userSearchMerc', methods=['GET','POST'])
def userSearchMerc():
    if request.method == 'POST':
        sub = request.form['sub']
        res = None
        if sub == 'merch':
            mname = request.form['mname']
            cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `merchant` WHERE `name` LIKE '%{mname}%' ")
            res = cmd.fetchall()
        elif sub == 'Buss':
            bname = request.form['bname']
            cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `merchant` WHERE `bname` LIKE '%{bname}%' ")
            res = cmd.fetchall()
        elif sub == 'Bplace':
            bplace = request.form['bplace']
            cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `merchant` WHERE `location` LIKE '%{bplace}%' ")
            res = cmd.fetchall()
        elif sub == 'Btype':
            btype = request.form['btype']
            cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `merchant` WHERE `btype` LIKE '%{btype}%' ")
            res = cmd.fetchall()
        return render_template('user-search-merch.html', res=res)
    else:
        return render_template('user-search-personnel.html')


if __name__ == '__main__':
    app.run(debug=True, port=5050)
