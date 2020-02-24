from flask import Flask, render_template, request, url_for
import folium
from twitter_lab import hidden
import urllib.request, urllib.parse, urllib.error
from twitter_lab import twurl
import json
import ssl
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


app = Flask(__name__)


@app.route('/')
def index():
    '''
    Function that returns web page, where has to
    be entered user name.
    '''
    return render_template('index.html')


def get_twitter_friends(acct):
    '''
    (str) -> dict

    Function that finds friends of the inputted user.
    '''
    TWITTER_URL = 'https://api.twitter.com/1.1/friends/list.json'

    # Ignore SSL certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    inputt = 0
    while inputt != 1:
        if (len(acct) < 1): break
        url = twurl.augment(TWITTER_URL,
                            {'screen_name': acct, 'count': '50'})
        connection = urllib.request.urlopen(url, context=ctx)
        data = connection.read().decode()
        
        inputt += 1
        new_js = json.loads(data)
    return new_js


def find_loc(new_js):
    '''
    (dict) -> dict

    Function that returns the locations of the users
    friends
    '''
    loc_user_dct = {}
    for i in range(len(new_js['users'])):
        try:
            key = new_js['users'][i]['location']
            value = new_js['users'][i]['screen_name']
            if key not in loc_user_dct.keys():
                loc_user_dct[key] = [value]
            else:
                loc_user_dct[key].append(value)
        except Exception:
            continue
    return loc_user_dct


def coordinates(loc_user_dct):
    '''
    (dict) -> dict

    Function that returns the dictionary with key
    that contains latitude and longitude of the
    friends of user and value is a list of
    friends that live in the same place.
    '''
    geo_dct = {}
    geolocator = Nominatim(user_agent="specify_your_app_name_here")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    for key, value in loc_user_dct.items():
        try:
            location = geolocator.geocode(key)
            tpl_loc = (location.latitude, location.longitude)
            geo_dct[tpl_loc] = value
        except Exception:
            continue
    new_dct = {'lat': [], 'lon': [], 'friends': []}
    for key, value in geo_dct.items():
        key_loc = list(key)
        new_dct['lat'].append(key_loc[0])
        new_dct['lon'].append(key_loc[1])
        new_dct['friends'].append(value)
    return new_dct


def create_map(total_dct):
    '''
    Function that creates html map
    with markers.
    '''
    lat = total_dct['lat']
    lon = total_dct['lon']
    friends = total_dct['friends']

    folium_map = folium.Map(tiles='Stamen Terrain')

    fg_fl = folium.FeatureGroup(name="Twitter friends")
    for lt, ln, fr in zip(lat, lon, friends):
        fg_fl.add_child(folium.Marker(location=[lt, ln],
                                      radius=10,
                                      popup=', '.join(fr),))
    folium_map.add_child(fg_fl)
    html_map = folium_map.get_root().render()
    return html_map



@app.route('/', methods=['POST'])
def create_web():
    '''
    Function that returns web page.
    '''
    try:
        acct = request.form['name']
        friends = get_twitter_friends(acct)
        loc_dct = find_loc(friends)
        total_dct = coordinates(loc_dct)
        contex = {"html_str_map": create_map(total_dct)}
        return render_template("locations.html", **contex)
    except Exception:
        return 'Such account does not exist!'


if __name__ == "__main__":
    app.run(debug=True)