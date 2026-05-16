-- Insert sample users
-- Password for all users: clinic123

INSERT INTO users (first_name, last_name, name, email, password, role, doctor_specialization) VALUES ('Clinic', 'Admin', 'Clinic Admin', 'admin@example.com', 'scrypt:32768:8:1$mUX86qGtZqu0zLHf$513a891eee6170b9bf445e97eda1e79b2a825ca0638e04a7bdc0663ff1e6387591d309a97b934769bbab00fda7d69187a1fbf784d7b2ab4674f530d0781b9b8e', 'admin', 'General Medicine');

INSERT INTO users (first_name, last_name, name, email, password, role, doctor_specialization) VALUES ('Patient', 'User', 'Patient User', 'user@example.com', 'scrypt:32768:8:1$mUX86qGtZqu0zLHf$513a891eee6170b9bf445e97eda1e79b2a825ca0638e04a7bdc0663ff1e6387591d309a97b934769bbab00fda7d69187a1fbf784d7b2ab4674f530d0781b9b8e', 'user', '');

COMMIT;
