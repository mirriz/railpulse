--Create Stations Table
CREATE TABLE stations (
    code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL -- 'Hub' or 'Spoke'
);

