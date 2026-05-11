-- Insert sample appointments

INSERT INTO appointments (user_id, staff_id, appointment_date, appointment_time, status) VALUES (3, 2, TO_DATE('2026-05-05', 'YYYY-MM-DD'), '10:30', 'Confirmed');

INSERT INTO appointments (user_id, staff_id, appointment_date, appointment_time, status) VALUES (3, 2, TO_DATE('2026-05-12', 'YYYY-MM-DD'), '14:00', 'Pending');

COMMIT;
