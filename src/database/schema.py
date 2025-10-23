"""
Database schema for AI call agent system
"""

CREATE_TABLES_SQL = """
-- Leads table
CREATE TABLE IF NOT EXISTS leads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    company VARCHAR(255),
    status ENUM('new', 'contacted', 'interested', 'not_interested', 'appointment_scheduled', 'callback_requested', 'do_not_call') DEFAULT 'new',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_phone (phone_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('active', 'paused', 'completed') DEFAULT 'active',
    max_concurrent_calls INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Call records table
CREATE TABLE IF NOT EXISTS call_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT,
    lead_id INT,
    phone_number VARCHAR(20) NOT NULL,
    channel_id VARCHAR(255),
    call_status ENUM('initiated', 'ringing', 'answered', 'completed', 'failed', 'busy', 'no_answer') DEFAULT 'initiated',
    duration INT DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    answered_at TIMESTAMP NULL,
    ended_at TIMESTAMP NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL,
    INDEX idx_campaign (campaign_id),
    INDEX idx_lead (lead_id),
    INDEX idx_status (call_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Conversation logs table
CREATE TABLE IF NOT EXISTS conversation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    call_record_id INT,
    speaker ENUM('agent', 'customer') NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (call_record_id) REFERENCES call_records(id) ON DELETE CASCADE,
    INDEX idx_call (call_record_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lead_id INT,
    call_record_id INT,
    appointment_date DATETIME NOT NULL,
    appointment_type VARCHAR(100),
    notes TEXT,
    status ENUM('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show') DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
    FOREIGN KEY (call_record_id) REFERENCES call_records(id) ON DELETE SET NULL,
    INDEX idx_lead (lead_id),
    INDEX idx_date (appointment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""
