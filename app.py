#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from db import app, db
from models import *
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

#To Run: FLASK_APP=app.py FLASK_ENV=development flask run
#Test Facebook link format - https://www.facebook.com/NightFlightOfficial/

moment = Moment(app)
app.config.from_object('config')
migrate = Migrate(app, db)

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
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
    flash('Venue could not be deleted!')
  finally:
    db.session.close()

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
      artist.seeking_description = form.seeking_description.data,
      artist.seeking_venue = bool(form.seeking_venue.data)
      
      db.session.commit()
      flash('Artist ' + artist.name + ' was successfully edited!')
    except:
      db.session.rollback()
      flash('Artist ' + artist.name + ' could not be edited!')
    finally:
      db.session.close()
  else:
    flash('Errors in validation')
  
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
      venue.seeking_description = form.seeking_description.data
      venue.seeking_talent = bool(form.seeking_talent.data)
      
      db.session.commit()
      flash('Venue ' + venue.name + ' was successfully edited!')
    except:
      db.session.rollback()
      flash('Venue ' + venue.name + ' could not be edited!')
    finally:
      db.session.close()
  else:
    flash('Errors in validation')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
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
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form.name + ' could not be listed.')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  
  error=False
  data=[]
  allShows = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Show.venue_id == Venue.id).all()

  for show in allShows:
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
    db.session.add(thisShow)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()

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
