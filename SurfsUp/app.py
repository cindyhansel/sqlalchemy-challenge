# Import the dependencies.
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
# Find the most recent date in table
def most_recent_date():
     # Create our session (link) from Python to the DB
    session = Session(engine)

    # Find the most recent date in table
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    
    # Close session after query
    session.close()

    return last_date

# Return a date that is one year less than the given date
def previous_year_date(date):
    # Subtract a year from the given date
    previous_year = dt.datetime.strptime(date, "%Y-%m-%d") - dt.timedelta(days=365)
    
    return previous_year



@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to the Hawaii Precipitation and Temperature API!<br/>"
        f"Available Routes:<br/>"
        f"Retrieve JSON list of precipitation observations from the most recent year:   /api/v1.0/precipitation<br/>"
        f"Retrieve JSON list of stations:    /api/v1.0/stations<br/>"
        f"Retrieve JSON list of temperature observations from the most recent year:   /api/v1.0/tobs<br/>"
        f"Retrieve statistics JSON of the most active station, from given start date (/yyyy-mm-dd) to the most recent date:   /api/v1.0/<start><br/>"
        f"Retrieve statistics JSON of the most active station, from given start date to a specific given end date (/yyyy-mm-dd/yyyy-mm-dd):   /api/v1.0/<start>/<end>"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list showing precipitation from the last year"""

    # Query precipitation data from last 12 months from the most recent date from Measurement table
    # Uses the functions most_recent_year and previous_year_date
    precipitation_query = session.query(Measurement.date, Measurement.prcp).\
                                filter(Measurement.date >= previous_year_date(most_recent_date())).all()

    # Close session after query
    session.close()

    # Create dictionary within a list for JSON
    precipitation_list = []
    for date, prcp in precipitation_query:
        precipitation_dict = {}
        precipitation_dict["Date"] = date
        precipitation_dict["Precipitation"] = prcp
        precipitation_list.append(precipitation_dict)

    return jsonify(precipitation_list)


@app.route("/api/v1.0/stations")
def stations():

    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of stations - including all info"""
   
    stations_query = session.query(Station.station, 
                                Station.name, 
                                Station.latitude, 
                                Station.longitude, 
                                Station.elevation).all()
   
    # Close the session after query
    session.close()

    # Create dictionary within a list for JSON
    stations_list = []
    for station, name, latitude, longitude, elevation in stations_query:
        stations_dict = {}
        stations_dict["Station"] = station
        stations_dict["Name"] = name
        stations_dict["Latitude"] = latitude
        stations_dict["Longitude"] = longitude
        stations_dict["Elevation"] = elevation
        stations_list.append(stations_dict)
   
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of temperature observations for the previous year"""

    # Find the most active station
    station_actions = session.query(Measurement.station, func.count(Measurement.date)).\
        group_by(Measurement.station).order_by(func.count(Measurement.date).desc()).all()
    most_active_station = station_actions[0][0]

    # Query temperature observations for the most recent 12 months
    # Using functions for most_recent_date and previous_year_date
    tobs_query = session.query(Measurement.date, Measurement.tobs).\
                        filter(Measurement.station == most_active_station).\
                        filter(Measurement.date >= previous_year_date(most_recent_date())).all()
       
    # Close the session after query
    session.close()

    # Create dictionary within a list for JSON
    tobs_list = []
    for date, temp in tobs_query:
        tobs_dict = {}
        tobs_dict["Date"] = date
        tobs_dict["Tobs"] = temp
        tobs_list.append(tobs_dict)
   
    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
# Accept both start and end and account for no end date submitted
# Initialize the inputs as None and fork off of the existence of the end variable
def stats_combined(start=None, end=None):

    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a JSON list of temperature statistics for a user defined time period"""

    if end == None:  
        stats_query = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
            filter(Measurement.date >= start).all()
    else:
        stats_query = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
            filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    
    # Close session after query
    session.close()

    # Create dictionary within a list for JSON
    stats_list = []
    for tmin, tmax, tavg in stats_query:
        stats_dict = {}
        stats_dict["Min"] = tmin
        stats_dict["Max"] = tmax
        stats_dict["Avg"] = tavg
        stats_list.append(stats_dict)

    return jsonify(stats_list)

if __name__ == '__main__':
    app.run(debug=True)
