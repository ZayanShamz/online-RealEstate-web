from flask import *
import pymysql
import ssl
import certifi
from geopy.geocoders import Nominatim
import os

app = Flask(__name__)
app.secret_key = "classified"


con = pymysql.connect(host='localhost', port=3306, user='root', password='root1234', db='realestate')
cmd = con.cursor()

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

        q1 ="SELECT `name` FROM `dealer` WHERE `login_id`=%s"
        cmd.execute(q1, (lid,))
        usr = cmd.fetchone()[0]

        q2 = "INSERT INTO `plot` VALUES(NULL, %s, %s, %s, %s, %s, %s, NULL, NULL, %s, 'pending', '0')"
        cmd.execute(q2, (lid, name, loc, area, plot_type, price, count))
        pid = str(con.insert_id())

        q3 = "INSERT INTO `plot_locations` VALUES(NULL, %s, %s, %s, %s, %s, %s, %s)"
        cmd.execute(q3, (pid, lati, long, loc, state, county, zipcode))

        c = 1
        for file in pfiles:
            print(f'Adding file {c}')

            # Use os.path.splitext to safely get the file extension
            _, ext = os.path.splitext(file.filename)


            fname = f"{usr}({lid})_{name}"
            print(f'Filename: {fname}')
            photo = f"{fname}-{c}{ext}"
            print(f'Photo: {photo}')

            image_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'plot')

            file_path = os.path.join(image_dir, photo)
            file.save(file_path)

            q4 = "insert into plot_images` VALUES(NULL, %s, %s)"
            cmd.execute(q4, (pid, photo))

            q5 = "update `plot` set `filename`=%s, `ext`=%s  WHERE `plot_id`=%s "
            cmd.execute(q5, (fname, ext, pid))
            con.commit()
            c += 1
        return "<script>alert('Plot Added Successfully');window.location='/userHome'</script>"
    else:
        return render_template('user-add-plot.html')
    
    