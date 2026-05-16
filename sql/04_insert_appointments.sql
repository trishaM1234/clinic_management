-- Insert sample appointments

INSERT INTO appointments (user_id, staff_id, appointment_date, appointment_time, status, checkup_type, checkup_notes) VALUES (2, 1, '2026-05-05', '10:30', 'Confirmed', 'Overall Check-up', 'Initial general check-up');

INSERT INTO appointments (user_id, staff_id, appointment_date, appointment_time, status, checkup_type, checkup_notes) VALUES (2, 1, '2026-05-12', '14:00', 'Pending', 'Follow-up Check-up', 'Follow-up visit');

COMMIT;
