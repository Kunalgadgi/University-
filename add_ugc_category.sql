-- Add ugc_category column to AdmissionApplication table
ALTER TABLE master_control_admissionapplication 
ADD COLUMN ugc_category VARCHAR(50) DEFAULT '';

-- The field will accept these values:
-- 'Category I (JRF)'
-- 'Category II (NET)' 
-- 'Category III (Ph.D. Only)'
-- 'Not Applicable'
