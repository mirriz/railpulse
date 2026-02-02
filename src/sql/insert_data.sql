-- Stations to monitor into Leeds
INSERT INTO stations (code, name, type) VALUES
('LDS', 'Leeds', 'Hub'), -- Leeds is focal station for this system
('MAN', 'Manchester Piccadilly', 'Spoke'),
('YRK', 'York', 'Spoke'),
('WKF', 'Wakefield Westgate', 'Spoke'),
('HGT', 'Harrogate', 'Spoke');

-- Arrivals to Leeds
INSERT INTO routes (origin_code, destination_code, label, avg_travel_time_mins, operator) VALUES
('MAN', 'LDS', 'West Line', 96, 'Transpennine'),
('YRK', 'LDS', 'East Line', 35, 'CrossCountry'),
('WKF', 'LDS', 'South Line', 14, 'LNER'),
('HGT', 'LDS', 'North Line', 36, 'Northern');

-- Dummy Incidents 
INSERT INTO incidents (route_id, type, severity, description, created_at) VALUES
((SELECT id FROM routes WHERE origin_code = 'MAN'), 'Crowding', 5, 'Standing room only', NOW()),
((SELECT id FROM routes WHERE origin_code = 'MAN'), 'Delay', 3, 'Signal failure near Huddersfield', NOW()),
((SELECT id FROM routes WHERE origin_code = 'YRK'), 'Facilities', 2, 'WiFi not working', NOW());