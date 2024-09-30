from flask import *
import pymysql
import ssl
import certifi
from geopy.geocoders import Nominatim
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "classified"


con = pymysql.connect(host='localhost', port=3306, user='root', password='root1234', db='realestate')
cmd = con.cursor()


# Create an SSL context using certifi's certificate bundle
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Pass the SSL context when initializing Nominatim
geoLocator = Nominatim(user_agent="realestate_app", ssl_context=ssl_context, timeout=10)

def calculate_age(dob):
    dob = datetime.strptime(dob, '%Y-%m-%d')
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age

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


@app.route('/last_url')
def last_url():
    last_url = session['last_url']
    return redirect(last_url)

# ------------------------------------- ADMIN - DEALER - FUNCTIONS -----------------------------------------------------

@app.route('/adminHome')
def adminHome():
    session['last_url'] = request.url
    return render_template("adminhome.html")


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
        return "<script>alert('Dealer Added');window.location='/adminHome'</script>"
    else:
        cmd.execute("SELECT * FROM `dealer`")
        res = cmd.fetchall()
        return render_template('admin-add-dealer.html', dealers=res)


@app.route('/viewDealerList', methods=['GET', 'POST'])
def viewDealerList():
    session['last_url'] = request.url
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

    # session['last_url'] = f'/viewDealer/{lid}'
    # print(session['last_url'])

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

    # Delete plot related records
    cmd.execute("SELECT `plot_id` FROM `plot` WHERE `login_id`=%s", (lid,))
    pids = [i[0] for i in cmd.fetchall()]

    if pids:
        pids.append(0)  # To avoid empty tuple issues in IN clause
        pids = tuple(pids)
    else:
        pids = (0, 0)

    # Fetch and delete images related to the plots
    cmd.execute(f"SELECT `filename` FROM `plot_images` WHERE `pid` IN %s", (pids,))
    filenames = [i[0] for i in cmd.fetchall()]
    for i in filenames:
        image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'plot')
        os.remove(os.path.join(image_dir, i))

    # Delete plot-related data
    cmd.execute("DELETE FROM `plot_images` WHERE `pid` IN %s", (pids,))
    cmd.execute("DELETE FROM `plot_locations` WHERE `pid` IN %s", (pids,))
    cmd.execute("DELETE FROM `plot_requests` WHERE `pid` IN %s", (pids,))
    cmd.execute("DELETE FROM `plot` WHERE `login_id`=%s", (lid,))


    # Delete rental related records
    # Fetch rental IDs for the given login ID
    cmd.execute("SELECT `rental_id` FROM `rental` WHERE `login_id`=%s", (lid,))
    rids = [i[0] for i in cmd.fetchall()]

    # Handle case where rental IDs are found
    if rids:
        rids.append(0)  # To prevent SQL error in IN clause when no rentals exist
        rids = tuple(rids)
    else:
        rids = (0, 0)

    # Fetch filenames of rental images
    cmd.execute(f"SELECT `filename` FROM `rental_images` WHERE `rid` IN %s", (rids,))
    rentalNames = [i[0] for i in cmd.fetchall()]

    # Remove each rental image file
    for i in rentalNames:
        image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'rentals')
        os.remove(os.path.join(image_dir, i))

    # Delete records from rental-related tables
    cmd.execute("DELETE FROM `rental_images` WHERE `rid` IN %s", (rids,))
    cmd.execute("DELETE FROM `rental_locations` WHERE `rid` IN %s", (rids,))
    cmd.execute("DELETE FROM `rental_requests` WHERE `rid` IN %s", (rids,))
    cmd.execute("DELETE FROM `rental` WHERE `login_id`=%s", (lid,))

    # Delete from `rental`, `dealer`, and `login` tables
    cmd.execute("DELETE FROM `dealer` WHERE `login_id`=%s", (lid,))
    cmd.execute("DELETE FROM `login` WHERE `lid`=%s", (lid,))

    con.commit()

    if aid == 1:
        print(f'Admin deleted dealer: {lid}')
        return redirect('/viewDealerList')
    else:
        return f"<script>alert('Profile Deleted');window.location='/'</script>"


@app.route('/editDealer/<lid>', methods=['GET', 'POST'])
def editDealer(lid):
    cmd.execute("SELECT * FROM `dealer` WHERE `login_id`='"+lid+"' ")
    res = cmd.fetchone()

    if request.method == 'POST':
        name = request.form['dealerName']
        email = request.form['dealerEmail']
        phone = request.form['dealerPhone']
        gender = request.form['gender']
        dob = request.form['dealerDob']

        cmd.execute("""
            UPDATE `dealer` SET `name`=%s, `email`=%s, `phone`=%s, `gender`=%s, `dob`=%s 
            WHERE `login_id`=%s
        """, (name, email, phone, gender, dob, lid))
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
        login_id = request.form['dealer']
        area = request.form['area']
        plot_type = request.form['ptype']
        price = request.form['price']

        # Location ::
        lati = request.form['lat']
        long = request.form['lon']

        loc = geoLocator.reverse(lati + "," + long)
        address = loc.raw['address']
        state = address.get('state', '')
        district = address.get('state_district', '')
        zipcode = address.get('postcode', '')

        pfiles = request.files.getlist('files')
        count = len(pfiles)

        cmd.execute("SELECT `name` FROM `dealer` WHERE `login_id`=%s", login_id)
        usr = cmd.fetchone()
        print(f"Dealer: {usr}")
        if usr:  # Check if usr is not None
            usr = usr[0]
        else:
            print("No dealer found with the given login_id")

        # Begin transaction
        
        con.begin()  # Start transaction

        # Insert into plot
        query1 = "INSERT INTO `plot` VALUES(NULL, %s, %s, %s, %s, %s, %s, %s, %s, '0', 'Available', '0')"
        values1 = (login_id, name, area, plot_type, price, loc, district, state)
        cmd.execute(query1, values1)
        pid = str(con.insert_id())

        # Insert into plot_locations
        cmd.execute("INSERT INTO `plot_locations` VALUES(NULL, %s, %s, %s, %s)", (pid, lati, long, zipcode))

        # Save images
        count = 0
        for file in pfiles:
            if file and file.filename:
                _, ext = os.path.splitext(file.filename)
                fname = f"{usr}({login_id})_{name}({count}){ext}"

                image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'plot')
                file_path = os.path.join(image_dir, fname)
                file.save(file_path)

                cmd.execute("INSERT INTO `plot_images` VALUES(NULL, %s, %s)", (pid, fname))
        cmd.execute("UPDATE `plot` SET `count` = %s WHERE `plot_id` = %s", (count, pid))
        con.commit()  # Commit transaction
        return "<script>alert('Plot Added Successfully');window.location='adminHome'</script>"
    else:
        return render_template("admin-add-plot.html", dealer=res)


@app.route('/viewPlotList', methods=['GET', 'POST'])
def viewPlotList():
    session['last_url'] = '/viewPlotList'

    if request.method == 'POST':
        pname = request.form['dname']
        cmd.execute(f"""
            SELECT plot.*, dealer.name, dealer.login_id 
            FROM plot INNER JOIN dealer ON plot.login_id = dealer.login_id 
            WHERE plot.name LIKE '%{pname}%' OR dealer.name LIKE '%{pname}%'
        """)
        res = cmd.fetchall()
        return render_template('admin-view-plotList.html', plots=res)
    else:
        cmd.execute("""
            SELECT plot.*, dealer.name, dealer.login_id 
            FROM plot INNER JOIN dealer ON plot.login_id = dealer.login_id
        """)
        res = cmd.fetchall()
        return render_template('admin-view-plotList.html', plots=res)


@app.route('/viewPlot/<pid>')
def viewPlot(pid):
    cmd.execute(f"""
        SELECT plot.*, dealer.login_id, dealer.name, dealer.email
        FROM plot INNER JOIN dealer ON plot.login_id = dealer.login_id
        WHERE plot.plot_id = '{pid}'
    """)
    res = cmd.fetchone()

    # Extract filenames into a list
    cmd.execute(f"""
        SELECT plot_images.filename FROM plot_images INNER JOIN plot ON plot.plot_id = plot_images.pid
        WHERE plot.plot_id = '{pid}'
    """)
    results = cmd.fetchall()
    filenames = [i[0] for i in results]

    
    cmd.execute(f"""
        SELECT plot_locations.* FROM plot_locations INNER JOIN plot ON plot.plot_id = plot_locations.pid
        WHERE plot.plot_id = '{pid}'
    """)
    location = cmd.fetchone()
    
    # Check if a location was found
    if location:
        latitude = location[2]  
        longitude = location[3] 
    else:
        print("No location found for the specified plot ID.")

    return render_template('admin-view-plot.html', plot=res, pics=filenames, lat=latitude, lon=longitude)


@app.route('/deletePlot/<pid>')
def deletePlot(pid):
    try:
        last_url = session['last_url']
        # Start transaction
        con.begin()

        # Fetch filenames associated with the plot
        cmd.execute("SELECT `filename` FROM `plot_images` WHERE `pid`=%s", (pid,))
        res = [i[0] for i in cmd.fetchall()]

        # Delete records from the database
        cmd.execute("DELETE FROM `plot` WHERE `plot_id`=%s", (pid,))
        cmd.execute("DELETE FROM `plot_locations` WHERE `pid`=%s", (pid,))
        cmd.execute("DELETE FROM `plot_images` WHERE `pid`=%s", (pid,))
        cmd.execute("DELETE FROM `plot_requests` WHERE `pid`=%s", (pid,))

        # Delete image files
        image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'plot')
        for filename in res:
            file_path = os.path.join(image_dir, filename)
            if os.path.exists(file_path):  # Check if the file exists
                os.remove(file_path)

        # Commit transaction
        con.commit()
        return redirect(last_url)

    except Exception as e:
        con.rollback()  # Rollback on error
        print(f"Error occurred during deletion: {e}")
        return "An error occurred while deleting the plot.", 500


@app.route('/editPlot/<pid>', methods=['GET', 'POST'])
def editPlot(pid):
    # Fetch dealers
    cmd.execute("SELECT `login_id`, `name` FROM `dealer`")
    dealers = cmd.fetchall()

    # Fetch plot details
    cmd.execute("""
        SELECT `plot`.*, `dealer`.`login_id`, `dealer`.`name`
        FROM `dealer`
        INNER JOIN `plot` ON `plot`.`login_id` = `dealer`.`login_id`
        WHERE `plot`.`plot_id` = %s
    """, (pid,))
    result = cmd.fetchone()

    if request.method == 'POST':
        name = request.form['pname']
        dealer_id = request.form['dealer']
        area = request.form['area']
        plot_type = request.form['ptype']
        price = request.form['price']

        lati = request.form['lat']
        long = request.form['lon']

        if lati or long:
            loc = geoLocator.reverse(f"{lati},{long}")
            address = loc.raw['address']
            state = address.get('state', '')
            district = address.get('district', '')
            zipcode = address.get('postcode', '')

            cmd.execute("""
                UPDATE `plot_locations` SET `latitude` = %s, `longitude` = %s, `zipcode` = %s
                WHERE `pid` = %s
            """, (lati, long, zipcode, pid))

            cmd.execute("UPDATE `plot` SET address=%s, state=%s, district=%s WHERE `plot_id`=%s ", (loc, state, district, pid))

        cmd.execute("""
            UPDATE `plot` SET `login_id`=%s, `name`=%s, `area`=%s, `type`=%s, `price`=%s WHERE `plot_id` = %s
        """, (dealer_id, name, area, plot_type, price, pid))
        con.commit()
        return f"<script>alert('Updated');window.location='/viewPlot/{pid}'</script>"

    else:
        return render_template('admin-edit-plot.html', plot=result, dealer=dealers)

 # pfiles = request.files.getlist('files')
        # if pfiles:
        #     for file in pfiles:
        #         ogc = int(ogc) + 1
        #         photo = fname + "-" + str(ogc) + ext
        #         file.save('static/images/plot/' + photo)

        #         cmd.execute("INSERT INTO `plot_images` VALUES(NULL, '"+pid+"', '"+photo+"')")
        #         con.commit()

        #     cmd.execute("UPDATE `plot` SET `count`='"+str(ogc)+"' WHERE `plot_id`='"+pid+"' ")
        #     con.commit()


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
        district = address.get('district', '')
        zipcode = address.get('postcode', '')

        pfiles = request.files.getlist('files')
        count = len(pfiles)

        cmd.execute("SELECT `name` FROM `dealer` WHERE `login_id`=%s", (dealer_id,))
        usr = cmd.fetchone()[0]

       
        con.begin()  # Start transaction

        cmd.execute("""
                INSERT INTO `rental` VALUES(NULL, %s, %s,  %s, %s, %s, %s, %s, %s, '0', 'Available','0')
                """ ,(dealer_id, name, area, storey, rent, loc, district, state))
        rid = str(con.insert_id())

        cmd.execute("INSERT INTO `rental_locations` VALUES(NULL, %s, %s, %s, %s)", (rid, lati, long, zipcode))

        c = 0
        for file in pfiles:
            if file and file.filename: 
                c += 1
                # Use os.path.splitext to safely get the file extension
                _, ext = os.path.splitext(file.filename)

                fname = f"{usr}({dealer_id})_{name}({c}){ext}"

                image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'rentals')
                file_path = os.path.join(image_dir, fname)
                file.save(file_path)

                cmd.execute("INSERT INTO `rental_images` VALUES(NULL, %s, %s)", (rid, fname))
        cmd.execute("UPDATE `rental` SET `count`=%s WHERE `rental_id`=%s", (c, rid)) 
        con.commit()
        return "<script>alert('Rental Added Successfully');window.location='adminHome'</script>"
    else:
        return render_template("admin-add-rental.html", dealer=res)


@app.route('/viewRentalList')
def viewRentalList():
    session['last_url'] = '/viewRentalList'

    cmd.execute("""
        SELECT `rental`.*, `dealer`.`name`, `dealer`.`login_id`
        FROM `rental`
        INNER JOIN `dealer` ON `rental`.`login_id` = `dealer`.`login_id`
    """)
    res = cmd.fetchall()
    return render_template('admin-view-rentalList.html', rentals=res)


@app.route('/viewRental/<rid>')
def viewRental(rid):

    cmd.execute("""
        SELECT `rental`.*, `dealer`.`login_id`, `dealer`.`name`, `dealer`.`email` FROM `dealer`, `rental`
        WHERE `rental`.`login_id` = `dealer`.`login_id` AND `rental`.`rental_id` = %s
    """, (rid,))
    res = cmd.fetchone()

    cmd.execute(f"""
        SELECT rental_images.filename FROM rental_images WHERE rid = %s
    """, (rid,))
    results = cmd.fetchall()
    # Extract filenames into a list
    filenames = [i[0] for i in results]

    cmd.execute("SELECT `latitude`,`longitude` FROM `rental_locations` WHERE `rid`=%s", (rid,))
    lat, lon = cmd.fetchone()
    return render_template('admin-view-rental.html', rental=res, lat=lat, lon=lon, pics=filenames)


@app.route('/deleteRental/<rid>')
def deleteRental(rid):

    last_url = session['last_url']
    
    # Start transaction
    con.begin()

    # Fetch filenames associated with the plot
    cmd.execute("SELECT `filename` FROM `rental_images` WHERE `rid`=%s", (rid,))
    res = [i[0] for i in cmd.fetchall()]

    # Delete records from the database
    cmd.execute("DELETE FROM `rental` WHERE `rental_id`=%s", (rid,))
    cmd.execute("DELETE FROM `rental_locations` WHERE `rid`=%s", (rid,))
    cmd.execute("DELETE FROM `rental_images` WHERE `rid`=%s", (rid,))
    cmd.execute("DELETE FROM `rental_requests` WHERE `rid`=%s", (rid,))

    # Delete image files
    image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'rentals')
    for filename in res:
        file_path = os.path.join(image_dir, filename)
        if os.path.exists(file_path):  # Check if the file exists
            os.remove(file_path)

    # Commit transaction
    con.commit()
    
    return redirect(last_url) 
   

@app.route('/editRental/<rid>', methods=['POST', 'GET'])
def editRental(rid):

    # Fetch dealers
    cmd.execute("SELECT `login_id`, `name` FROM `dealer`")
    dealers = cmd.fetchall()

    # Fetch plot details
    cmd.execute("""
        SELECT `rental`.*, `dealer`.`login_id`, `dealer`.`name`
        FROM `dealer`
        INNER JOIN `rental` ON `rental`.`login_id` = `dealer`.`login_id`
        WHERE `rental`.`rental_id` = %s
    """, (rid,))
    result = cmd.fetchone()

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
            district = address.get('district', '')
            zipcode = address.get('postcode', '')

            cmd.execute("""
                UPDATE `rental_locations` SET `latitude` = %s, `longitude` = %s, `zipcode` = %s WHERE `rid` = %s
            """, (lati, long, zipcode, rid))

            cmd.execute("""
                UPDATE `rental` SET address=%s, state=%s, district=%s WHERE `rental_id`=%s 
            """, (loc, state, district, rid))

        cmd.execute("""
            UPDATE `rental` SET `login_id`=%s, `name`=%s,`area`=%s, `storey`=%s,`rent`=%s WHERE `rental_id`=%s 
        """, (dealer_id, name, area, storey, rent, rid))

        con.commit()
        return f"<script>alert('Updated');window.location='/viewRental/{rid}'</script>"
    else:
        return render_template('admin-edit-rental.html', rental=result, dealer=dealers)


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

        _, ext = os.path.splitext(file.filename)
        photo = f"{name}{ext}"

        image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'engineers')
        file.save(os.path.join(image_dir, photo))

        cmd.execute("""
            INSERT INTO `engineer` VALUES(NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s )
        """, (name, exp, discipline, email, phone, gender, dob, loc, photo))
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
    else:
        cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `engineer`")
        res = cmd.fetchall()
    return render_template('admin-view-engList.html', res=res)


@app.route('/viewEngineer/<eid>')
def viewEngineer(eid):
    cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `engineer` WHERE `eng_id`={eid} ")
    res = cmd.fetchone()
    return render_template('admin-view-eng.html', eng=res)


@app.route('/editEngineer/<eid>', methods=['GET', 'POST'])
def editEngineer(eid):
    cmd.execute(f"select filename from engineer where eng_id={eid}") 
    curr_pic = cmd.fetchone()[0]
    if request.method == 'POST':
        name = request.form['ename']
        gender = request.form['gender']
        dob = request.form['dob']
        phone = request.form['phone']
        email = request.form['email']
        discipline = request.form['disc']
        exp = request.form['exp']

        address = request.form['address']
        lati = request.form['lat']
        long = request.form['lon']
        if lati and long:
            address = geoLocator.reverse(lati + "," + long)

        cmd.execute("""
            UPDATE `engineer` SET `name`=%s, `exp`=%s, `discipline`=%s,`email`=%s, `phone`=%s, `gender`=%s, `dob`=%s, `place`=%s
            WHERE `eng_id`=%s
        """, (name, exp, discipline, email, phone, gender, dob, address, eid))

        file = request.files['file']
        image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'engineers')
        if file:
            os.remove(os.path.join(image_dir, curr_pic))
            _, ext = os.path.splitext(file.filename)
            photo = f"{name}{ext}"
            file.save(os.path.join(image_dir, photo))

            cmd.execute("UPDATE `engineer` SET `filename`=%s WHERE `eng_id`=%s ", (photo, eid))

        con.commit()
        return redirect(f"/viewEngineer/{eid}")
    else:
        cmd.execute("SELECT * FROM `engineer` WHERE `eng_id`='"+eid+"'")
        res = cmd.fetchone()
        return render_template('admin-edit-eng.html', eng=res)


@app.route('/deleteEngineer/<eid>')
def deleteEngineer(eid):
    cmd.execute("SELECT `filename` FROM `engineer` WHERE `eng_id`=%s ", (eid,))
    res = cmd.fetchone()[0]
    if res:
        image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'engineers')
        os.remove(os.path.join(image_dir, res))
    cmd.execute("DELETE FROM `engineer` WHERE `eng_id`=%s", (eid,))
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
        _, ext = os.path.splitext(file.filename)
        photo = f"{name}{ext}"
        image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'merchant')
        file.save(os.path.join(image_dir, photo))

        cmd.execute("INSERT INTO `merchant` VALUES(NULL, %s, %s, %s, %s, %s, %s, %s, %s )", (name, dob, email, phone, bname, btype, loc, photo))
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
        return render_template('admin-view-merchList.html', res=res)
    else:
        cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `merchant`")
        res = cmd.fetchall()
        return render_template('admin-view-merchList.html', res=res)


@app.route('/viewMerchant/<mid>')
def viewMerchant(mid):
    cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `merchant` WHERE `merc_id`={mid}")
    res = cmd.fetchone()
    return render_template('admin-view-merch.html', merch=res)


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

        cmd.execute("""
            UPDATE `merchant` SET `name`=%s, `dob`=%s, `email`=%s, `phone`=%s,
            `bname`=%s, `btype`=%s, `location`=%s WHERE `merc_id`=%s
        """, (name, dob, email, phone, bname, btype, loc, mid))  

        file = request.files['file']
        if file:
            image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'merchant')
            os.remove(os.path.join(image_dir, fname))

            _, ext = os.path.splitext(file.filename)
            photo = f"{name}{ext}"
            file.save(os.path.join(image_dir, photo))
            cmd.execute("UPDATE `merchant` SET `filename`=%s WHERE `merc_id`=%s", (photo, mid))
        con.commit()
        return redirect(f"/viewMerchant/{mid}")

    else:
        cmd.execute("SELECT * FROM `merchant` WHERE `merc_id`='"+mid+"'")
        res = cmd.fetchone()
        return render_template('admin-edit-merch.html', merch=res)


@app.route('/deleteMerchant/<mid>')
def deleteMerchant(mid):
    cmd.execute(f"SELECT `filename` FROM `merchant` WHERE `merc_id`={mid}")
    res = cmd.fetchone()[0]
    
    if res:
        image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'merchant')
        os.remove(os.path.join(image_dir, res))
    cmd.execute(f"DELETE FROM `merchant` WHERE `merc_id`={mid}")
    con.commit()
    return redirect(url_for('viewMerchants'))


# ----------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------- user ---------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


@app.route('/userHome')
def userHome():
    session['last_url'] = '/userHome'
    if request.method == 'POST':
        pass
    else:
        return render_template("userhome.html")


@app.route('/userProfile')
def userProfile():
    lid = session['lid']
    session['last_url'] = request.url

    cmd.execute("SELECT * FROM `dealer` WHERE `login_id`=%s", (lid,))
    dealer = cmd.fetchone()
    dealer = dealer + (calculate_age(dealer[-2]),)

    cmd.execute("SELECT `plot_id`,`plot`.`name`,`address` FROM `dealer`, `plot` WHERE \
    `plot`.`login_id`=`dealer`.`login_id` AND `plot`.`login_id`=%s ", (lid,))
    plots = cmd.fetchall()

    cmd.execute("SELECT `rental_id`,`rental`.`name`,`address`,`status` FROM `dealer`, `rental` \
    WHERE `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`login_id`=%s", (lid,))
    rentals = cmd.fetchall()

    return render_template('user-profile.html', dealer=dealer, plots=plots, rentals=rentals)

@app.route('/userEdit', methods=['GET', 'POST'])
def userEdit():
    lid = session['lid']
    cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)),'%Y') + 0 AS age FROM `dealer` WHERE `login_id`={lid}")
    user = cmd.fetchone()

    if request.method == 'POST':
        name = request.form['dealerName']
        email = request.form['dealerEmail']
        phone = request.form['dealerPhone']
        gender = request.form['gender']
        dob = request.form['dealerDob']

        query = "UPDATE dealer SET name=%s, email=%s, phone=%s, gender=%s, dob=%s WHERE login_id=%s"
        cmd.execute(query, (name, email, phone, gender, dob, lid))
        con.commit()
        return f"<script>alert('Updated');window.location='/userProfile'</script>"
    else:
        return render_template('user-edit.html', dealer=user)


@app.route('/userViewRequests/<item>/<item_id>', methods=['GET', 'POST'])
def userViewRequests(item, item_id):
    lid = session['lid']
    if item == 'plot':
        cmd.execute("SELECT plot.name, dealer.name, plot_requests.* from plot, plot_requests, dealer WHERE\
                     plot.plot_id=plot_requests.pid and plot_requests.dealer_id=dealer.login_id and plot.login_id=%s", (lid,))
        plots = cmd.fetchall()
       
        return render_template('user-view-requests.html', res=plots, item=item)
    if item == 'rental':
        cmd.execute("SELECT rental.name, dealer.name, rental_requests.* from rental, rental_requests, dealer WHERE\
                     rental.rental_id=rental_requests.rid and rental_requests.dealer_id=dealer.login_id and rental.login_id=%s", (lid,))
        rentals = cmd.fetchall()
      
        return render_template('user-view-requests.html', res=rentals, item=item)
    return render_template('user-view-requests.html')


@app.route('/userAcceptRequest/<item>/<item_id>/<name>/<dealer>/<did>')
def userAcceptRequest(item, item_id, dealer, did, name):
    lid = session['lid']
    dealer_name = dealer
    dealer_id = did
    name = name
   
    if item == 'plot':
        cmd.execute("SELECT filename, id FROM plot_images WHERE plot_images.pid = %s", (item_id,))
        file_data = [ i for i in cmd.fetchall()]
        if file_data:
            count = 1
            for filename, plot_id in file_data:
                _, ext = os.path.splitext(filename)
                new_name = f"{dealer_name}({dealer_id})_{name}({count}){ext}"

                cmd.execute("update plot_images set filename=%s WHERE id=%s", (new_name, plot_id))

                image_dir = os.path.join(os.path.dirname(__file__),'static', 'images', 'plot')
                current_file_path = os.path.join(image_dir, filename)
                new_file_path = os.path.join(image_dir, new_name)

                # Rename the file
                if os.path.exists(current_file_path):
                    os.rename(current_file_path, new_file_path)
                        
                count += 1
        cmd.execute("update plot set status='Sold', login_id=%s, requests='0' WHERE plot_id=%s", (dealer_id, item_id))
        cmd.execute("delete from plot_requests WHERE pid=%s ", (item_id,))
        con.commit()
    elif item =='rental':
        cmd.execute("insert into rented values (NULL, %s, %s, %s, CURTIME(), CURDATE())", (item_id, lid, dealer_id, ))
        cmd.execute("update rental set status='Rented', requests='0' WHERE rental_id=%s", (item_id,))
        cmd.execute("delete from rental_requests WHERE rid=%s ", (item_id,))
        con.commit()
    return redirect(request.referrer)

@app.route('/userRejectRequest/<item>/<item_id>/<dealer_id>')
def userRejectRequest(item, item_id, dealer_id):

    if item == 'plot':
        # Update the requests count in the plot table after withdrawing a request.
        cmd.execute("SELECT `requests` FROM `plot` WHERE `plot_id`=%s", (item_id,))
        rqst = int(cmd.fetchone()[0])
        rqst -= 1
        cmd.execute("UPDATE `plot` SET `requests`=%s WHERE `plot_id`=%s", (rqst, item_id))

        # Delete the request from the plot_requests table.
        cmd.execute("DELETE FROM `plot_requests` WHERE `pid`=%s AND `dealer_id`=%s ", (item_id, dealer_id))
        con.commit()

    elif item =='rental':
        cmd.execute("SELECT `requests` FROM `rental` WHERE `rental_id`=%s", (item_id,))
        rqst = int(cmd.fetchone()[0])
        rqst -= 1

        cmd.execute("UPDATE `rental` SET `requests`=%s WHERE `rental_id`=%s", (rqst, item_id))
        cmd.execute("DELETE FROM `rental_requests` WHERE `rid`=%s AND `dealer_id`=%s", (item_id, dealer_id))
        con.commit()

    return redirect(request.referrer)


# ------------------------------------------- USER - Plot ---------------------------------------------------
@app.route('/userAddPlot', methods=['POST', 'GET'])
def userAddPlot():
    lid = session['lid']
    last_url = session['last_url']
    if request.method == 'POST':
        name = request.form['pname']
        area = request.form['area']
        plot_type = request.form['ptype']
        price = request.form['price']

        # Location ::
        lati = request.form['lat']
        long = request.form['lon']

        loc = geoLocator.reverse(lati + "," + long)
        address = loc.raw['address']
        state = address.get('state', '')
        district = address.get('state_district', '')
        zipcode = address.get('postcode', '')

        pfiles = request.files.getlist('files')
        count = len(pfiles)

        cmd.execute("SELECT `name` FROM `dealer` WHERE `login_id`=%s", lid)
        usr = cmd.fetchone()
        if usr:  # Check if usr is not None
            usr = usr[0]
        else:
            print("No dealer found with the given login_id")

        # Begin transaction
        con.begin() 

        # Insert into plot
        query1 = "INSERT INTO `plot` VALUES(NULL, %s, %s, %s, %s, %s, %s, %s, %s, NULL, 'Available', '0')"
        values1 = (lid, name, area, plot_type, price, loc, district, state)
        cmd.execute(query1, values1)
        pid = str(con.insert_id())

        # Insert into plot_locations
        cmd.execute("INSERT INTO `plot_locations` VALUES(NULL, %s, %s, %s, %s)", (pid, lati, long, zipcode))

        # Save images
        count = 0
        for file in pfiles:
            if file and file.filename:
                count += 1
                _, ext = os.path.splitext(file.filename)
                fname = f"{usr}({lid})_{name}({count}){ext}"

                image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'plot')
                file_path = os.path.join(image_dir, fname)
                file.save(file_path)

                cmd.execute("INSERT INTO `plot_images` VALUES(NULL, %s, %s)", (pid, fname))

        cmd.execute("UPDATE `plot` SET `count`=%s WHERE `plot_id`=%s", (count, pid))
        con.commit()  # Commit transaction
        return f"<script>alert('Plot Added Successfully');window.location='{last_url}'</script>"
    else:
        return render_template('user-add-plot.html')


@app.route('/userPlot/<pid>')
def userPlot(pid):
    lid = session['lid']

    cmd.execute(f"""
        SELECT plot.*, dealer.login_id, dealer.name, email, phone
        FROM plot INNER JOIN dealer ON plot.login_id = dealer.login_id
        WHERE plot.plot_id = '{pid}'
    """)
    res = cmd.fetchone()

    # Extract filenames into a list
    cmd.execute(f"""
        SELECT plot_images.filename FROM plot_images INNER JOIN plot ON plot.plot_id = plot_images.pid
        WHERE plot.plot_id = '{pid}'
    """)
    results = cmd.fetchall()
    filenames = [i[0] for i in results]
    
    cmd.execute(f"""
        SELECT plot_locations.* FROM plot_locations INNER JOIN plot ON plot.plot_id = plot_locations.pid
        WHERE plot.plot_id = '{pid}'
    """)
    location = cmd.fetchone()
    
    # Check if a location was found
    if location:
        latitude = location[2]  
        longitude = location[3] 
    else:
        print("No location found for the specified plot ID.")


    cmd.execute("""
        select * from plot_requests where pid=%s and dealer_id=%s;
        """, (pid, lid))
    req = cmd.fetchone()

    return render_template('user-view-plot.html', plot=res, lid=lid, lat=latitude, lon=longitude, pics=filenames, req=req)


@app.route('/userEditPlot/<pid>', methods=['GET','POST'])
def userEditPlot(pid):
    cmd.execute("""
        SELECT `plot`.*, `dealer`.`login_id`, `dealer`.`name`
        FROM `dealer`
        INNER JOIN `plot` ON `plot`.`login_id` = `dealer`.`login_id`
        WHERE `plot`.`plot_id` = %s
    """, (pid,))
    result = cmd.fetchone()

    if request.method == 'POST':
        name = request.form['pname']
        area = request.form['area']
        plot_type = request.form['ptype']
        price = request.form['price']

        lati = request.form['lat']
        long = request.form['lon']

        if lati or long:
            loc = geoLocator.reverse(f"{lati},{long}")
            address = loc.raw['address']
            state = address.get('state', '')
            district = address.get('district', '')
            zipcode = address.get('postcode', '')

            cmd.execute("""
                UPDATE `plot_locations` SET `latitude` = %s, `longitude` = %s, `zipcode` = %s
                WHERE `pid` = %s
            """, (lati, long, zipcode, pid))

            cmd.execute("UPDATE `plot` SET address=%s, state=%s, district=%s WHERE `plot_id`=%s ", (loc, state, district, pid))

        cmd.execute("""
            UPDATE `plot` SET  `name`=%s, `area`=%s, `type`=%s, `price`=%s WHERE `plot_id` = %s
        """, (name, area, plot_type, price, pid))
        con.commit()
        return f"<script>alert('Updated');window.location='/userPlot/{pid}'</script>"

    else:
        return render_template('user-edit-plot.html', plot=result)


@app.route('/plotSearch', methods=['GET','POST'])
def plotSearch():
    temp = "srch"
    lid = str(session['lid'])
    session['last_url'] = '/plotSearch'

    if request.method == 'POST':
        sub = request.form['sub']

        # search by plot name
        if sub == 'all':
            print('Searching all plots')
            cmd.execute(f"""
                SELECT plot.*, dealer.name
                FROM plot INNER JOIN dealer ON plot.login_id = dealer.login_id 
                WHERE plot.login_id != %s AND plot.status='Available'
            """, (lid,))
            res = cmd.fetchall()
            return render_template("user-view-plots.html", plots=res)
        
        elif sub == 'srch':
            pname = request.form['pname']
            if pname:
                cmd.execute(f"""
                    SELECT plot.*, dealer.name
                    FROM plot INNER JOIN dealer ON plot.login_id = dealer.login_id 
                    WHERE plot.name LIKE '%{pname}%' OR plot.address LIKE '%{pname}%'
                    AND plot.status='Available'
                """)
                res = cmd.fetchall()
                if res:
                    return render_template("user-view-plots.html", plots=res, temp=temp)
                else:
                    return "<script>alert('No search result');window.location='/plotSearch'</script>"
            else:
                return "<script>alert('Enter property name or place!');window.location='/plotSearch'</script>"

        # search by selection
        elif sub == 'srch2':
            print('Searching by selection')
            ptype = request.form['type']
            price = request.form['price']
            area = request.form['area']
            price_min, price_max = map(int, price.split('AND'))  
            area_min, area_max = map(int, area.split('AND')) 

            if ptype == 'any':
                query = """
                    SELECT `plot`.*, `dealer`.`name` 
                    FROM `plot` 
                    INNER JOIN `dealer` ON `plot`.`login_id` = `dealer`.`login_id`
                    WHERE `area` BETWEEN %s AND %s 
                    AND `price` BETWEEN %s AND %s
                    AND plot.status='Available'
                """
                params = (area_min, area_max, price_min, price_max)
            else:
                query = """
                    SELECT `plot`.*, `dealer`.`name` 
                    FROM `plot` 
                    INNER JOIN `dealer` ON `plot`.`login_id` = `dealer`.`login_id`
                    WHERE `area` BETWEEN %s AND %s 
                    AND `price` BETWEEN %s AND %s 
                    AND `type` = %s
                    AND plot.status='Available'
                """
                params = (area_min, area_max, price_min, price_max, ptype)
            
            cmd.execute(query, params)
            res = cmd.fetchall()
            if res:
                return render_template("user-view-plots.html", plots=res, temp=temp)
            else:
                return "<script>alert('No search result');window.location='/plotSearch'</script>"
    else:
        return render_template('user-search-prop.html')


@app.route('/plotRequest/<pid>')
def plotRequest(pid):
    lid = session['lid']

    # Update the requests count in the plot table after making a request.
    cmd.execute("SELECT `requests` FROM `plot` WHERE `plot_id`=%s", (pid,))
    rqst = int(cmd.fetchone()[0])
    rqst += 1
    cmd.execute("UPDATE `plot` SET `requests`=%s WHERE `plot_id`=%s", (rqst, pid))

    # Insert a new row into the plot_requests table. This will mark the plot as requested by the current user.
    cmd.execute("INSERT INTO `plot_requests` VALUES(NULL, %s, %s, CURDATE(), CURTIME())", (pid, lid))
    con.commit()
    return redirect(request.referrer)


@app.route('/plotWithdrawRequest/<pid>')
def plotWithdrawRequest(pid):
    lid = session['lid']

    # Update the requests count in the plot table after withdrawing a request.
    cmd.execute("SELECT `requests` FROM `plot` WHERE `plot_id`=%s", (pid,))
    rqst = int(cmd.fetchone()[0])
    rqst -= 1
    cmd.execute("UPDATE `plot` SET `requests`=%s WHERE `plot_id`=%s", (rqst, pid))

    # Delete the request from the plot_requests table.
    cmd.execute("DELETE FROM `plot_requests` WHERE `pid`=%s AND `dealer_id`=%s ", (pid, lid))
    con.commit()

    return redirect(request.referrer)


# ---------------------------------------- USER - Rental ------------------------------------

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
        district = address.get('district', '')
        zipcode = address.get('postcode', '')

        pfiles = request.files.getlist('files')

        cmd.execute("SELECT `name` FROM `dealer` WHERE `login_id`=%s", (lid,))
        usr = cmd.fetchone()[0]

       
        con.begin()  # Start transaction
        query = "INSERT INTO `rental` VALUES(NULL, %s, %s,  %s, %s, %s, %s, %s, %s, NULL, 'Available','0')"
        cmd.execute(query, (lid, name, area, storey, rent, loc, district, state))
                   
        rid = str(con.insert_id())

        cmd.execute("INSERT INTO `rental_locations` VALUES(NULL, %s, %s, %s, %s)", (rid, lati, long, zipcode))

        c = 0
        for file in pfiles:
            if file and file.filename:
                c += 1
                # Use os.path.splitext to safely get the file extension
                _, ext = os.path.splitext(file.filename)

                fname = f"{usr}({lid})_{name}({c}){ext}"

                image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'rentals')
                file_path = os.path.join(image_dir, fname)
                file.save(file_path)

                cmd.execute("INSERT INTO `rental_images` VALUES(NULL, %s, %s)", (rid, fname))

        cmd.execute("UPDATE `rental` SET `count`=%s WHERE `rental_id`=%s", (c, rid))
        con.commit()
        return "<script>alert('Rental Added Successfully');window.location='/userProfile'</script>"
    else:
        return render_template("user-add-rental.html")
    

@app.route('/userRental/<rid>')
def userRental(rid):
    lid = session['lid']

    cmd.execute(f"""
        SELECT rental.*, dealer.login_id, dealer.name, email, phone
        FROM rental INNER JOIN dealer ON rental.login_id = dealer.login_id
        WHERE rental.rental_id =%s
    """, (rid,))
    res = cmd.fetchone()

    # Extract filenames into a list
    cmd.execute(f"""
        SELECT rental_images.filename FROM rental_images INNER JOIN rental ON rental.rental_id = rental_images.rid
        WHERE rental.rental_id = '{rid}'
    """)
    results = cmd.fetchall()
    filenames = [i[0] for i in results]
    
    # Get rental location data
    cmd.execute(f"""
        SELECT rental_locations.* FROM rental_locations INNER JOIN rental ON rental.rental_id = rental_locations.rid
        WHERE rental.rental_id = '{rid}'
    """)
    location = cmd.fetchone()
    if location:
        latitude = location[2]  
        longitude = location[3] 
    else:
        print("No location found for the specified plot.")

    cmd.execute("""
        select * from rental_requests where rid=%s and dealer_id=%s;
        """, (rid, lid))
    req = cmd.fetchone()

    return render_template('user-view-rental.html', rental=res, lid=lid, lat=latitude, lon=longitude, pics=filenames, req=req)


@app.route('/userEditRental/<rid>', methods=['POST', 'GET'])
def userEditRental(rid):

    cmd.execute("""
        SELECT `rental`.*, `dealer`.`login_id`, `dealer`.`name`
        FROM `dealer`
        INNER JOIN `rental` ON `rental`.`login_id` = `dealer`.`login_id`
        WHERE `rental`.`rental_id` = %s
    """, (rid,))
    res = cmd.fetchone()

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
            district = address.get('district', '')
            zipcode = address.get('postcode', '')

            cmd.execute("""
                UPDATE `rental_locations` SET `latitude` = %s, `longitude` = %s, `zipcode` = %s
                WHERE `rid` = %s
            """, (lati, long, zipcode, rid))

            cmd.execute("UPDATE `rental` SET address=%s, state=%s, district=%s WHERE `rental_id`=%s ", (loc, state, district, rid))
      

        cmd.execute("""
            UPDATE `rental` SET  `name`=%s, `area`=%s, `storey`=%s, `rent`=%s WHERE `rental_id` = %s
        """, (name, area, storey, rent, rid))
        con.commit()
        return f"<script>alert('Updated');window.location='/userRental/{rid}'</script>"
    else:
        return render_template('user-edit-rental.html', rental=res)


@app.route('/rentalSearch', methods=['GET','POST'])
def rentalSearch():
    lid = session['lid']
    session['last_url'] = request.url
    if request.method == 'POST':
        session['last_url'] = request.url
        print(f"Last URL: {session['last_url']}")
        click = request.form['btnclick']
        if click == 'all':
            cmd.execute(f"""
                SELECT rental.*, dealer.name
                FROM rental INNER JOIN dealer ON rental.login_id = dealer.login_id 
                WHERE rental.login_id != '{lid}'
                AND rental.status = 'Available'
            """)
            res = cmd.fetchall()
            print(f'all = {res}')
            return render_template("user-view-rentals.html", rentals=res)
        
        elif click == 'srch':
            rname = request.form['rname']
            if rname:
                cmd.execute(f"""
                    SELECT rental.*, dealer.name
                    FROM rental INNER JOIN dealer ON rental.login_id = dealer.login_id 
                    WHERE rental.name LIKE '%{rname}%' OR rental.address LIKE '%{rname}%'
                    AND rental.status = 'Available'
                """)
                res = cmd.fetchall()
                if res:
                    return render_template("user-view-rentals.html", rentals=res)
                else:
                    return "<script>alert('No search result');window.location='/rentalSearch'</script>"
            else:
                print("NO RESULT")
                return "<script>alert('No search result');window.location='/rentalSearch'</script>"

        else:
            print('Searching by selection')
            storey = request.form['storey']

            price = request.form['rprice']
            area = request.form['rarea']
            price_min, price_max = map(int, price.split('AND'))  
            area_min, area_max = map(int, area.split('AND')) 

            if storey == 'any':
                query = """
                    SELECT `rental`.*, `dealer`.`name` 
                    FROM `rental` 
                    INNER JOIN `dealer` ON `rental`.`login_id` = `dealer`.`login_id`
                    WHERE `area` BETWEEN %s AND %s 
                    AND `rent` BETWEEN %s AND %s
                    AND rental.status = 'Available'
                """
                params = (area_min, area_max, price_min, price_max)
            else:
                query = """
                    SELECT `rental`.*, `dealer`.`name` 
                    FROM `rental` 
                    INNER JOIN `dealer` ON `rental`.`login_id` = `dealer`.`login_id`
                    WHERE `area` BETWEEN %s AND %s 
                    AND `rent` BETWEEN %s AND %s 
                    AND `storey` = %s
                    AND rental.status = 'Available'
                """
                params = (area_min, area_max, price_min, price_max, storey)
            
            cmd.execute(query, params)
            res = cmd.fetchall()
            if res:
                return render_template("user-view-rentals.html", rentals=res)
            else:
                return "<script>alert('No search result');window.location='/rentalSearch'</script>"
    else:
        return render_template('user-search-prop.html')


@app.route('/rentalRequest/<rid>')
def rentalRequest(rid):
    lid = str(session['lid'])

    # Fetch the current number of requests
    cmd.execute("SELECT `requests` FROM `rental` WHERE `rental_id`=%s", (rid,))
    rqst = int(cmd.fetchone()[0])

    # Increment the request count
    rqst += 1

    # Update the requests count
    cmd.execute("UPDATE `rental` SET `requests`=%s WHERE `rental_id`=%s", (rqst, rid))

    # Insert the new rental request
    cmd.execute("INSERT INTO `rental_requests` VALUES(NULL, %s, %s, CURDATE(), CURTIME())", (rid, lid))

    # Commit the transaction
    con.commit()
    return redirect(request.referrer)


@app.route('/rentalWithdrawRequest/<rid>')
def rentalWithdrawRequest(rid):
    lid = str(session['lid'])

    cmd.execute("SELECT `requests` FROM `rental` WHERE `rental_id`=%s", (rid,))
    rqst = int(cmd.fetchone()[0])
    rqst -= 1

    cmd.execute("UPDATE `rental` SET `requests`=%s WHERE `rental_id`=%s", (rqst, rid))
    cmd.execute("DELETE FROM `rental_requests` WHERE `rid`=%s AND `dealer_id`=%s", (rid, lid))
    con.commit()
    return redirect(request.referrer)


@app.route('/userViewLeasedList')
def userViewLeasedList():
    session['last_url'] = request.url
    lid = session['lid']
    cmd.execute(f"""
            SELECT rental.*, dealer.name
            FROM rented
            INNER JOIN rental ON rented.rental_id = rental.rental_id
            INNER JOIN dealer ON rental.login_id = dealer.login_id
            WHERE rented.tenant_id = %s;
            """, (lid,))
    rentals = cmd.fetchall()
    return render_template('user-view-leased.html', rentals=rentals)


@app.route('/userCancelLease/<rid>')
def userCancelLease(rid):
    cmd.execute("UPDATE `rental` SET `status`='Available' WHERE `rental_id`=%s", (rid,))
    cmd.execute("DELETE FROM `rented` WHERE `rental_id`=%s", (rid,))
    con.commit()
    return redirect(request.referrer)


# ---------------------- USER - DEALER -------------------------------          
@app.route('/userViewDealer/<did>')
def userViewDealer(did):

    session['last_url'] = f'/userViewDealer/{did}'

    cmd.execute("SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)),'%Y') + 0 AS age FROM `dealer` WHERE `login_id`='"+did+"'")
    res = cmd.fetchone()

    cmd.execute("SELECT `plot_id`,`plot`.`name`,`address`,`dealer`.`name` FROM `dealer`, `plot` WHERE \
    `plot`.`login_id`=`dealer`.`login_id` AND `plot`.`login_id`='"+did+"' ")
    plots = cmd.fetchall()

    cmd.execute("SELECT `rental_id`,`rental`.`name`,`address`,`dealer`.`name` FROM `dealer`, `rental` \
    WHERE `rental`.`login_id`=`dealer`.`login_id` AND `rental`.`login_id`='"+did+"'")
    rentals = cmd.fetchall()

    return render_template('user-view-dealer.html', dealer=res, plots=plots, rentals=rentals)


# -----------------------------------------------------------------------------
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

        elif sub == 'discipline':
            disc = request.form['disc']
            cmd.execute(f"SELECT *, DATE_FORMAT(FROM_DAYS(DATEDIFF(NOW(),`dob`)), '%Y') + 0 AS age FROM `engineer` WHERE `discipline` LIKE '%{disc}%' ")
            res = cmd.fetchall()

        return render_template('user-view-engineers.html', res=res)
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

        return render_template('user-view-merchants.html', res=res)
    else:
        return render_template('user-search-personnel.html')


if __name__ == '__main__':
    app.run(debug=True, port=5050)
