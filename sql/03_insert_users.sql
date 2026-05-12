-- Insert sample users
-- Password for all users: clinic123

INSERT INTO users (name, email, password, role) VALUES ('Clinic Admin', 'admin@example.com', 'scrypt:32768:8:1$mUX86qGtZqu0zLHf$513a891eee6170b9bf445e97eda1e79b2a825ca0638e04a7bdc0663ff1e6387591d309a97b934769bbab00fda7d69187a1fbf784d7b2ab4674f530d0781b9b8e', 'admin');

INSERT INTO users (name, email, password, role) VALUES ('Front Desk Staff', 'staff@example.com', 'scrypt:32768:8:1$mUX86qGtZqu0zLHf$513a891eee6170b9bf445e97eda1e79b2a825ca0638e04a7bdc0663ff1e6387591d309a97b934769bbab00fda7d69187a1fbf784d7b2ab4674f530d0781b9b8e', 'staff');

INSERT INTO users (name, email, password, role) VALUES ('Patient User', 'user@example.com', 'scrypt:32768:8:1$mUX86qGtZqu0zLHf$513a891eee6170b9bf445e97eda1e79b2a825ca0638e04a7bdc0663ff1e6387591d309a97b934769bbab00fda7d69187a1fbf784d7b2ab4674f530d0781b9b8e', 'user');

COMMIT;
