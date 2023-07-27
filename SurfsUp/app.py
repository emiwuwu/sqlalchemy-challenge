# Import the dependencies.
from flask import Flask, jsonify
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt
from datetime import timedelta

#################################################
# Database Setup
#################################################
engine= create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base= automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
station= Base.classes.station
measurement= Base.classes.measurement

# Create our session (link) from Python to the DB
session= Session(engine)

#################################################
# Flask Setup
#################################################
app= Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route('/')
def index():
    # Define a list of available routes in the API
    available_routes = [
        '/api/v1.0/precipitation',  
        '/api/v1.0/stations',      
        '/api/v1.0/tobs',           
        '/api/v1.0/<start>',        
        '/api/v1.0/<start>/<end>'   
    ]
    
    # Return the list of available routes as a JSON response
    return jsonify({"available_routes": available_routes})

@app.route('/api/v1.0/precipitation')
def get_precipitition():
    # Get the most recent date from the 'Measurement' table in the database
    most_recent_date = session.query(func.max(measurement.date)).scalar()

    # Convert the most recent date from string to a Python date object
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d').date()
    
    # Calculate the date one year ago from the most recent date
    one_year_ago = most_recent_date - timedelta(days=365)

    # Query precipitation data from the database for the last year
    results = session.query(measurement.date, measurement.prcp).filter(measurement.date >= one_year_ago).all()

    # Convert the query results into a dictionary with date as key and precipitation as value
    precipitation_data = {date: prcp for date, prcp in results}
    
    # Return the precipitation data as a JSON response
    return jsonify(precipitation_data)

@app.route('/api/v1.0/stations')
def get_stations():
    # Query the distinct station names from the 'Station' table in the database
    stations = session.query(station.station).distinct().all()

    # Extract the station names from the query results and store them in a list
    station_data = [row.station for row in stations]

    # Return the list of station names as a JSON response
    return jsonify(station_data)

@app.route('/api/v1.0/tobs')
def get_most_active_station_data():
    # Query the most active station along with the count of its occurrences in the 'Measurement' table
    most_active_station = session.query(
        measurement.station,
        func.count(measurement.station).label('station_count')
    ).group_by(measurement.station).order_by(func.count(measurement.station).desc()).first()

    # Query the most recent date associated with the most active station
    most_recent_date = session.query(func.max(measurement.date)).filter(
        measurement.station == most_active_station.station
    ).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d').date()
    
    # Calculate the date one year ago from the most recent date
    one_year_ago = most_recent_date - timedelta(days=365)
    
    # Query temperature observation data for the most active station for the last year
    results = session.query(
        measurement.tobs
    ).filter(
        measurement.station == most_active_station.station,
        measurement.date >= one_year_ago,
        measurement.date <= most_recent_date
    ).all()
    
    # Extract the temperature observations from the query results and store them in a list
    most_active_station_data = [row.tobs for row in results]

    # Return the list of temperature observations as a JSON response
    return jsonify(most_active_station_data)

@app.route('/api/v1.0/<start>')
@app.route('/api/v1.0/<start>/<end>')
def get_temperature_stats(start=None, end=None):
    
    # Convert the date strings to datetime objects
    start_date = dt.datetime.strptime(start, '%Y-%m-%d').date()
    end_date = dt.datetime.strptime(end, '%Y-%m-%d').date() if end else None
    
    # Query for the temperature statistics based on the specified start and end dates
    if end_date:
        results = session.query(
            func.min(measurement.tobs).label('TMIN'),
            func.avg(measurement.tobs).label('TAVG'),
            func.max(measurement.tobs).label('TMAX')
        ).filter(
            measurement.date >= start_date,
            measurement.date <= end_date
        ).all()
    else:
        results = session.query(
            func.min(measurement.tobs).label('TMIN'),
            func.avg(measurement.tobs).label('TAVG'),
            func.max(measurement.tobs).label('TMAX')
        ).filter(
            measurement.date >= start_date
        ).all()

    # Convert the results to a list of dictionaries
    temperature_data = [
        {'TMIN': result.TMIN, 'TAVG': result.TAVG, 'TMAX': result.TMAX}
        for result in results
    ]
    return jsonify(temperature_data)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)