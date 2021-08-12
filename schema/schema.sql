CREATE DATABASE rfh_indices_proj;

CREATE TABLE file_servers (
	server_id SERIAL PRIMARY KEY  NOT NULL,
	server_name VARCHAR UNIQUE NOT NULL,
	server_path VARCHAR
);

CREATE TABLE imagery_extents (
	imagery_id SERIAL PRIMARY KEY NOT NULL,
	imagery_extent GEOMETRY,
	imagery_date TIMESTAMP,
	imagery_server INTEGER REFERENCES file_servers(server_id) ON UPDATE CASCADE ON DELETE SET NULL,
	imagery_path VARCHAR,
	imagery_desc VARCHAR DEFAULT NULL
);

CREATE TABLE imagery_bands_path (
	path_id SERIAL PRIMARY KEY NOT NULL,
	imagery_id INTEGER REFERENCES imagery_extents(imagery_id) ON UPDATE CASCADE ON DELETE CASCADE,
	band_name VARCHAR NOT NULL,
	band_path VARCHAR
);

CREATE TABLE missing_aoi (
    aoi_id SERIAL PRIMARY KEY NOT NULL,
    aoi jsonb
);

CREATE TABLE missing_aoi_form (
    form_id SERIAL PRIMARY KEY NOT NULL,
    aoi_id INTEGER REFERENCES missing_aoi (aoi_id) ON UPDATE CASCADE ON DELETE CASCADE,
    full_name VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    phone VARCHAR NOT NULL
);
