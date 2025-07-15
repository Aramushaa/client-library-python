USE arrowhead;

CREATE TABLE IF NOT EXISTS interface (
  id INT PRIMARY KEY,
  interface_name VARCHAR(255) NOT NULL UNIQUE
);

INSERT IGNORE INTO interface (id, interface_name) VALUES
  (1, 'HTTP-SECURE-JSON'),
  (2, 'HTTP-INSECURE-JSON');
