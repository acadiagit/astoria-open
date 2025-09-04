-- Path: /db/schemas/init_schema.sql
-- Filename: init_schema.sql
-- Directory: /db/schemas
-- Purpose: Initialize database schema for PostgreSQL

-- History table for storing query history
CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sql_query TEXT,
    response_text TEXT NOT NULL,
    results_json TEXT,
    user_id TEXT,
    session_id TEXT
);

-- Create index on timestamp for efficient retrieval
CREATE INDEX IF NOT EXISTS idx_query_history_timestamp ON query_history (query_timestamp DESC);

-- Vessels table
CREATE TABLE IF NOT EXISTS vessels (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    vessel_type TEXT,
    flag TEXT,
    year_built INTEGER,
    tonnage NUMERIC(10, 2),
    length NUMERIC(8, 2),
    beam NUMERIC(8, 2),
    draft NUMERIC(8, 2),
    status TEXT,
    last_port TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on vessel name
CREATE INDEX IF NOT EXISTS idx_vessels_name ON vessels (name);

-- Voyages table
CREATE TABLE IF NOT EXISTS voyages (
    id SERIAL PRIMARY KEY,
    vessel_id INTEGER NOT NULL REFERENCES vessels(id),
    departure_port TEXT,
    departure_date TIMESTAMP,
    arrival_port TEXT,
    arrival_date TIMESTAMP,
    cargo TEXT,
    notes TEXT,
    status TEXT,
    CONSTRAINT fk_vessel_voyages FOREIGN KEY (vessel_id) REFERENCES vessels(id) ON DELETE CASCADE
);

-- Create indices for voyages
CREATE INDEX IF NOT EXISTS idx_voyages_vessel_id ON voyages (vessel_id);
CREATE INDEX IF NOT EXISTS idx_voyages_departure_date ON voyages (departure_date);
CREATE INDEX IF NOT EXISTS idx_voyages_arrival_date ON voyages (arrival_date);

-- Maintenance table
CREATE TABLE IF NOT EXISTS maintenance (
    id SERIAL PRIMARY KEY,
    vessel_id INTEGER NOT NULL REFERENCES vessels(id),
    maintenance_date TIMESTAMP NOT NULL,
    maintenance_type TEXT NOT NULL,
    description TEXT,
    cost NUMERIC(10, 2),
    completed BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_vessel_maintenance FOREIGN KEY (vessel_id) REFERENCES vessels(id) ON DELETE CASCADE
);

-- Create indices for maintenance
CREATE INDEX IF NOT EXISTS idx_maintenance_vessel_id ON maintenance (vessel_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_date ON maintenance (maintenance_date);

-- Crew table
CREATE TABLE IF NOT EXISTS crew (
    id SERIAL PRIMARY KEY,
    vessel_id INTEGER NOT NULL REFERENCES vessels(id),
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    date_joined TIMESTAMP,
    date_left TIMESTAMP,
    nationality TEXT,
    license_number TEXT,
    CONSTRAINT fk_vessel_crew FOREIGN KEY (vessel_id) REFERENCES vessels(id) ON DELETE CASCADE
);

-- Create index for crew
CREATE INDEX IF NOT EXISTS idx_crew_vessel_id ON crew (vessel_id);

-- Sample data for vessels
INSERT INTO vessels (name, vessel_type, flag, year_built, tonnage, length, beam, draft, status)
VALUES 
    ('ABBIE', 'Cargo', 'USA', 1872, 120.5, 65.3, 18.2, 8.5, 'Active'),
    ('ANNIE', 'Schooner', 'Canada', 1880, 95.0, 58.7, 16.9, 7.8, 'Active'),
    ('ATLANTIC', 'Passenger', 'USA', 1903, 1000.0, 150.0, 40.0, 15.0, 'Retired'),
    ('LIBERTY', 'Tanker', 'Panama', 1920, 2500.0, 200.0, 45.0, 18.0, 'Retired'),
    ('MACHIAS', 'Fishing', 'USA', 1945, 85.0, 50.0, 15.0, 6.5, 'Active')
ON CONFLICT (id) DO NOTHING;

-- Sample data for voyages
INSERT INTO voyages (vessel_id, departure_port, departure_date, arrival_port, arrival_date, cargo, status)
VALUES 
    (1, 'Machias', '1872-06-15', 'Boston', '1872-06-18', 'Lumber', 'Completed'),
    (1, 'Boston', '1872-06-25', 'Machias', '1872-06-28', 'General goods', 'Completed'),
    (2, 'Halifax', '1882-07-10', 'Portland', '1882-07-15', 'Fish', 'Completed'),
    (3, 'New York', '1903-08-01', 'Liverpool', '1903-08-12', 'Passengers', 'Completed'),
    (5, 'Machias', '1945-05-01', 'Portland', '1945-05-03', 'Fish', 'Completed')
ON CONFLICT (id) DO NOTHING;

-- Sample data for maintenance
INSERT INTO maintenance (vessel_id, maintenance_date, maintenance_type, description, cost, completed)
VALUES 
    (1, '1872-09-10', 'Hull repair', 'Repaired damaged hull section', 250.00, TRUE),
    (2, '1882-10-15', 'Mast replacement', 'Replaced broken mast', 350.00, TRUE),
    (3, '1904-02-20', 'Engine overhaul', 'Complete engine maintenance', 1200.00, TRUE),
    (5, '1946-03-25', 'Annual inspection', 'Regular inspection and minor repairs', 150.00, TRUE)
ON CONFLICT (id) DO NOTHING;

-- Sample data for crew
INSERT INTO crew (vessel_id, name, position, date_joined, nationality)
VALUES 
    (1, 'John Smith', 'Captain', '1872-05-01', 'American'),
    (1, 'William Jones', 'First Mate', '1872-05-01', 'American'),
    (2, 'Robert Brown', 'Captain', '1880-06-15', 'Canadian'),
    (3, 'James Wilson', 'Chief Engineer', '1903-07-20', 'British'),
    (5, 'Michael Johnson', 'Captain', '1945-04-10', 'American')
ON CONFLICT (id) DO NOTHING;
