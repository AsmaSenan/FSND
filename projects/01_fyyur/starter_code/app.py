#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import  func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from datetime import datetime, timezone
# from model import *


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
# TODO DONE: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:3911986@localhost:5432/fyyurapp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.



class Show_list(db.Model):
  __tablename__ = 'show_list'
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id', ondelete='CASCADE'), primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id', ondelete='CASCADE'), primary_key=True)
  start_time = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), primary_key=True)


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    genres = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    # TODO DONE: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    venues = db.relationship('Venue', secondary = "show_list" , cascade="save-update, merge, delete, delete-orphan", single_parent=True, backref=db.backref('artists', cascade='all', lazy=True))

    # TODO DONE: implement any missing fields, as a database migration using Flask-Migrate

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):

  date = dateutil.parser.parse(str(value))
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
def stringToList(string):
    string = string.replace('{', '') 
    string = string.replace('}', '')
    listRes = list(string.split(","))
    return listRes

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  areas = Venue.query.distinct(Venue.city, Venue.state)
  data = []
  for area in areas:
    venues = db.engine.execute(' SELECT venue.id, venue.name, venue.city, venue.state, (SELECT COUNT(*) AS "num_upcoming_shows" FROM show_list WHERE venue_id = venue.id AND start_time>now()) FROM venue WHERE venue.city LIKE %s AND venue.state LIKE %s ORDER BY num_upcoming_shows DESC;', area.city, area.state)
    data.append(
      {"city": area.city, "state": area.state, "venues": venues ,}
    )
  return render_template('pages/venues.html', areas = data )

@app.route('/venues/search', methods=['POST'])
def search_venues(): 
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  data = []
  for venue in venues:
    venue_shows = db.session.query(Show_list.venue_id, Show_list.start_time).join(Venue).filter(venue.id == Show_list.venue_id)
    upcoming_shows = list( filter( lambda x: x.start_time >= datetime.now(timezone.utc), venue_shows ) )
    data.append(
    {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(upcoming_shows)
    })
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  
  venue = Venue.query.get(venue_id)
  venue_shows = db.session.query(Show_list.venue_id, Show_list.artist_id, Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Show_list.start_time).join(Artist).filter(Show_list.venue_id == venue_id)
  # .filter(Show_list.venue_id == venue.id) since the models already made with relationship between them no need to this filter 

  #count number of past shows and upcoming 
  past_shows = list( filter( lambda x: x.start_time < datetime.now(timezone.utc), venue_shows ) )
  upcoming_shows = list( filter( lambda x: x.start_time >= datetime.now(timezone.utc), venue_shows ) )
  
 
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": stringToList(venue.genres),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }


  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  form = VenueForm(request.form, meta={"csrf": False})
  if form.validate():
    try:
      new_venue = Venue(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        address = request.form['address'],
        phone = request.form['phone'],
        website = request.form['website'],
        facebook_link = request.form['facebook_link'],
        image_link = request.form['image_link'],
        genres = request.form.getlist('genres'),
        seeking_talent = True if request.form.get('seeking_talent') == 'y' else False,
        seeking_description = request.form['seeking_description'],
      )
      db.session.add(new_venue)
      db.session.commit()
    except Exception as e:
      error = True
      db.session.rollback()
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.' +str(e))
    finally:
      db.session.close()
    if not error:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  else:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.'+ str(form.errors))
      return render_template('forms/new_venue.html', form = VenueForm())
  
  return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
  deletedVenue = Venue.query.filter_by(id=venue_id).first()
  if not deletedVenue:
    flash('The Venue Id is invalid')
    return render_template("errors/404.html"), 404
  else:
    try:
      Venue.query.filter_by(id=venue_id).delete()
      db.session.commit()
      flash('The Venue has been successfully deleted!')
    except Exception as e:
      db.session.rollback()
      flash('An error occurred. Venue '+ deletedVenue.name + 'could not be deleteed')
    finally:
      db.session.close()

  return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = db.session.query(Artist.id, Artist.name)
  data = []
  for artist in artists:
    artist_shows = db.session.query(Show_list.start_time).join(Artist).filter(Show_list.start_time >= datetime.now(timezone.utc)).filter(artist.id == Show_list.artist_id).count()
    data.append(
    {
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": artist_shows
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  data = []
  for artist in artists:
    artist_shows = db.session.query(Show_list.start_time).join(Artist).filter(Show_list.start_time >= datetime.now(timezone.utc)).filter(artist.id == Show_list.artist_id).count()
    data.append(
    {
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": artist_shows
    })
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term = search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)

  artist_shows = db.session.query(Show_list.artist_id, Show_list.venue_id, Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), Show_list.start_time).join(Venue).filter(Show_list.artist_id == artist_id)

  #count number of past shows and upcoming 
  past_shows = list( filter( lambda x: x.start_time < datetime.now(timezone.utc), artist_shows ) )
  upcoming_shows = list( filter( lambda x: x.start_time >= datetime.now(timezone.utc), artist_shows ) )
 
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": stringToList(artist.genres),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_talent": artist.seeking_talent,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)



#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  if not artist:
    flash('The Artist Id is invalid')
    return render_template("errors/404.html"), 404
  else:
    form = ArtistForm()
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data =artist.state
    form.phone.data = artist.phone
    form.website.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link  
    form.genres.data = artist.genres
    form.seeking_talent.data =artist.seeking_talent
    form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  form = ArtistForm(request.form, meta={"csrf": False})
  if form.validate():
    try:
      artist = db.session.query(Artist).filter_by(id=artist_id).one()
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.website = request.form['website']
      artist.facebook_link = request.form['facebook_link']
      artist.image_link = request.form['image_link']
      artist.genres = request.form.getlist('genres')
      artist.seeking_talent = True if request.form.get('seeking_talent') == 'y' else False
      artist.seeking_description = request.form['seeking_description']
      db.session.add(artist)
      db.session.commit()
    except Exception as e:
      error = True
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.' +str(e))
    finally:
      db.session.close()
    if not error:
      flash('Artist ' + request.form['name']  + ' was successfully updated!')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  else:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.'+ str(form.errors))
      return render_template('forms/edit_artist.html', form = ArtistForm(), artist=Artist.query.get(artist_id))
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if not venue:
    flash('The Venue Id is invalid')
    return render_template("errors/404.html"), 404
  else:
    form = VenueForm()
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data =venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.website.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link  
    form.genres.data = venue.genres
    form.seeking_talent.data =venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  form = VenueForm(request.form, meta={"csrf": False})
  if form.validate():
    try:
      venue = db.session.query(Venue).filter_by(id=venue_id).one()
      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.website = request.form['website']
      venue.facebook_link = request.form['facebook_link']
      venue.image_link = request.form['image_link']
      venue.genres = request.form.getlist('genres')
      venue.seeking_talent = True if request.form.get('seeking_talent') == 'y' else False
      venue.seeking_description = request.form['seeking_description']
      db.session.add(venue)
      db.session.commit()
    except Exception as e:
      error = True
      db.session.rollback()
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.' +str(e))
    finally:
      db.session.close()
    if not error:
      flash('Venue ' + request.form['name']  + ' was successfully updated!')
  else:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.'+ str(form.errors))
      return render_template('forms/edit_venue.html', form = VenueForm(), venue=Venue.query.get(venue_id))
  return redirect(url_for('show_venue', venue_id = venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  
  error = False
  form = ArtistForm(request.form, meta={"csrf": False})
  if form.validate():
    try:
      new_artist = Artist(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        # address = request.form['address'],
        phone = request.form['phone'],
        website = request.form['website'],
        facebook_link = request.form['facebook_link'],
        image_link = request.form['image_link'],
        genres = request.form.getlist('genres'),
        seeking_talent = True if request.form.get('seeking_talent') == 'y' else False,
        seeking_description = request.form['seeking_description'],
      )
      db.session.add(new_artist)
      db.session.commit()
    except Exception as e:
      error = True
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.' +str(e))
    finally:
      db.session.close()
    if not error:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  else:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.'+ str(form.errors))
      return render_template('forms/new_artist.html', form = ArtistForm())
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  query = db.session.query(Show_list.venue_id, Show_list.artist_id, Show_list.start_time, Venue.name.label('venue_name'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link')).join(Venue).join(Artist).all()
  return render_template('pages/shows.html', shows=query)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  form = ShowForm(request.form, meta={"csrf": False})
  if form.validate():
    try:
      new_show = Show_list(
        venue_id = request.form['venue_id'],
        artist_id = request.form['artist_id'],
        start_time = request.form['start_time'],
      )
      db.session.add(new_show)
      db.session.commit()
    except Exception as e:
      error = True
      db.session.rollback()
      flash('An error occurred. Show could not be listed.' +str(e))
    finally:
      db.session.close()
    if not error:
      flash('Show was successfully listed!')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  else:
      flash('An error occurred. Show could not be listed.'+ str(form.errors))
      return render_template('forms/new_show.html', form = ShowForm())
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
