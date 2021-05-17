#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

#FLASK_APP=app.py FLASK_ENV=development flask run

#https://www.facebook.com/NightFlightOfficial/

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String(120)))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, unique=False, default=True)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
      return f'<Venue {self.name} {self.city} {self.state} {self.address} {self.phone} {self.image_link} {self.facebook_link} {self.genres} {self.website_link} {self.seeking_talent} {self.seeking_description} {self.shows}>'

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, unique=False, default=True)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
      return f'<Artist {self.name} {self.city} {self.state} {self.phone} {self.image_link} {self.facebook_link} {self.genres} {self.website_link} {self.seeking_venue} {self.seeking_description} {self.shows}>'

class Show(db.Model):
    __tablename__ = 'Show'
  
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
      return f'<Show {self.artist_id} {self.venue_id} {self.start_time}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

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
  # num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  areas = Venue.query.distinct('city', 'state')
  for area in areas:
    
    areaVenues = Venue.query.filter(Venue.city == area.city, Venue.state ==area.state).all()
    record = {
      "city": area.city,
      "state": area.state,
      "venues": [],
    }

    for venue in areaVenues:
      thisVenue = {
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(venue.shows)
      }
      record['venues'].append(thisVenue)
    
    data.append(record)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  search_term=request.form.get('search_term')
  searchResult = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  response={
    "count": len(searchResult),
    "data": []
  }

  for venue in searchResult:
    thisVenue={
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(venue.shows)
    }
    response['data'].append(thisVenue)

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id

  upcoming=[]
  past=[]
  
  upcoming_shows = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Show.venue_id == Venue.id).filter(Show.venue_id == venue_id, Show.artist_id == Artist.id, Show.start_time >= datetime.now()).all()
  upcoming_shows_count = len(upcoming_shows)

  past_shows = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Show.venue_id == Venue.id).filter(Show.venue_id == venue_id, Show.artist_id == Artist.id, Show.start_time < datetime.now()).all()
  past_shows_count = len(past_shows)

  thisVenue = Venue.query.get(venue_id)
  
  for show in upcoming_shows:
    thisShow={
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time), format='full'),
      "artist_id": show.artist_id,
      "artist_name": show.artist.name
    }
    upcoming.append(thisShow)

  for show in past_shows:
    thisShow={
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time), format='full'),
      "artist_id": show.artist_id,
      "artist_name": show.artist.name
    }
    past.append(thisShow)
  
  data = {
    "name": thisVenue.name,
    "id": thisVenue.id,
    "genres": thisVenue.genres,
    "city": thisVenue.city,
    "address": thisVenue.address,
    "phone": thisVenue.phone,
    "website_link": thisVenue.website_link,
    "facebook_link": thisVenue.facebook_link,
    "seeking_talent": thisVenue.seeking_talent,
    "seeking_description": thisVenue.seeking_description,
    "image_link": thisVenue.image_link,
    "upcoming_shows": upcoming,
    "past_shows": past,
    "upcoming_shows_count": upcoming_shows_count,
    "past_shows_count": past_shows_count
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
  try:
    thisVenue = Venue(name=request.form.get('name'),
        city=request.form.get('city'),
        state=request.form.get('state'),
        address=request.form.get('address'),
        phone=request.form.get('phone'),
        image_link=request.form.get('image_link'),
        facebook_link=request.form.get('facebook_link'),
        genres=request.form.getlist('genres'),
        website_link=request.form.get('website_link'),
        seeking_talent=request.form.get('seeking_talent', default=False, type=bool),
        seeking_description=request.form.get('seeking_description'),
        shows=request.form.getlist('shows')
    )
    db.session.add(thisVenue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  
  # on successful db insert, flash success
  flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  Venue.query.filter_by(id=venue_id).delete()
  db.session.commit()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  artists = Artist.query.all()
  for artist in artists:
    record = {
      "id": artist.id,
      "name": artist.name
    }
    data.append(record)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  search_term=request.form.get('search_term')
  searchResult = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  response={
    "count": len(searchResult),
    "data": []
  }

  for artist in searchResult:
    thisArtist={
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(artist.shows)
    }
    response['data'].append(thisArtist)
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id

  upcoming=[]
  past=[]

  past_shows = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id).filter(Show.venue_id == Venue.id, Show.artist_id == artist_id, Show.start_time < datetime.now()).all()
  past_shows_count = len(past_shows)
  
  upcoming_shows = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id).filter(Show.venue_id == Venue.id, Show.artist_id == artist_id, Show.start_time >= datetime.now()).all()
  upcoming_shows_count = len(upcoming_shows)

  thisArtist = Artist.query.get(artist_id)

  for show in past_shows:
    thisShow={
      'venue_image_link': show.venue.image_link,
      'start_time': format_datetime(str(show.start_time), format='full'),
      'venue_id': show.venue_id,
      'venue_name': show.venue.name
    }
    past.append(thisShow)

  for show in upcoming_shows:
    thisShow={
      'venue_image_link': show.venue.image_link,
      'start_time': format_datetime(str(show.start_time), format='full'),
      'venue_id': show.venue_id,
      'venue_name': show.venue.name
    }
    upcoming.append(thisShow)
  
  data = {
    "name": thisArtist.name,
    "id": thisArtist.id,
    "genres": thisArtist.genres,
    "city": thisArtist.city,
    "phone": thisArtist.phone,
    "website_link": thisArtist.website_link,
    "facebook_link": thisArtist.facebook_link,
    "seeking_venue": thisArtist.seeking_venue,
    "seeking_description": thisArtist.seeking_description,
    "upcoming_shows_count": upcoming_shows_count,
    "upcoming_shows": upcoming,
    "past_shows_count": past_shows_count,
    "past_shows": past
  }
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  
  artist = Artist.query.get_or_404(artist_id)

  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(request.form, meta={"csrf": False})

  if form.validate():
    try:
      
      artist.name = form.name.data,
      artist.city = form.city.data,
      artist.state = form.state.data,
      artist.phone = form.phone.data,
      artist.image_link = form.image_link.data,
      artist.genres = form.genres.data
      artist.facebook_link = form.facebook_link.data,
      artist.website_link = form.website_link.data,
      artist.seeking_talent = form.seeking_venue.data,
      artist.seeking_description = form.seeking_description.data
      
      db.session.commit()
      flash('Artist ' + artist.name + ' was successfully edited!')
    except ValueError:
      error = True
      db.session.rollback()
    finally:
      db.session.close()
  else:
    message=[]
    print(form.errors.items())
    
    for field, errors in form.errors.items():
      message.append(form[field].label + ', '.join(errors))
      flash('Errors: ' + '|'.join(message))
  
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(request.form, meta={"csrf": False})

  if form.validate():
    try:
      
      venue.name = form.name.data,
      venue.city = form.city.data,
      venue.state = form.state.data,
      venue.address = form.address.data
      venue.phone = form.phone.data,
      venue.image_link = form.image_link.data,
      venue.genres = form.genres.data
      venue.facebook_link = form.facebook_link.data,
      venue.website_link = form.website_link.data,
      venue.seeking_talent = form.seeking_talent.data,
      venue.seeking_description = form.seeking_description.data
      
      db.session.commit()
      flash('Venue ' + venue.name + ' was successfully edited!')
    except ValueError:
      error = True
      db.session.rollback()
    finally:
      db.session.close()
  else:
    message=[]
    print(form.errors.items())
    
    for field, errors in form.errors.items():
      message.append(form[field].label + ', '.join(errors))
      flash('Errors: ' + '|'.join(message))

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  print("Hit artist Get")
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  
  error = False
  try:
    thisArtist = Artist(name=request.form.get('name'),
        city=request.form.get('city'),
        state=request.form.get('state'),
        phone=request.form.get('phone'),
        image_link=request.form.get('image_link'),
        facebook_link=request.form.get('facebook_link'),
        genres=request.form.getlist('genres'),
        website_link=request.form.get('website_link'),
        seeking_venue=request.form.get('seeking_venue', default=False, type=bool),
        seeking_description=request.form.get('seeking_description'),
        shows=request.form.getlist('shows')
    )
    db.session.add(thisArtist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  

  error=False
  data=[]
  allShows = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Show.venue_id == Venue.id).all()

  #print(allShows[0].artist.name)

  for show in allShows:
    print(show.artist.name)
    record = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
    }
    data.append(record)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False 
  try:
  
    thisShow = Show(
      artist_id=request.form.get("artist_id"),
      venue_id=request.form.get("venue_id"),
      start_time=request.form.get("start_time")
    )
    print(thisShow)
    db.session.add(thisShow)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()

  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
