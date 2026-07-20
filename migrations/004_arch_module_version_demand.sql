-- Migration: 004_arch_module_version_demand
-- Date: 2026-07-08
-- Description: Add version tracking and demand relation fields to module, function, and parameter tables

-- Add new fields to module table
ALTER TABLE module
ADD COLUMN create_version TEXT DEFAULT '1.0.0',
ADD COLUMN version_record TEXT DEFAULT '[]',
ADD COLUMN demand_relation TEXT DEFAULT '[]',
ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE,
ADD COLUMN deleted_at TIMESTAMP;

-- Add new fields to function table
ALTER TABLE function
ADD COLUMN create_version TEXT DEFAULT '1.0.0',
ADD COLUMN version_record TEXT DEFAULT '[]',
ADD COLUMN demand_relation TEXT DEFAULT '[]',
ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE,
ADD COLUMN deleted_at TIMESTAMP;

-- Add new fields to parameter table
ALTER TABLE parameter
ADD COLUMN create_version TEXT DEFAULT '1.0.0',
ADD COLUMN version_record TEXT DEFAULT '[]',
ADD COLUMN demand_relation TEXT DEFAULT '[]',
ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE,
ADD COLUMN deleted_at TIMESTAMP;

-- Create indexes for soft delete queries
CREATE INDEX idx_module_is_deleted ON module(is_deleted);
CREATE INDEX idx_function_is_deleted ON function(is_deleted);
CREATE INDEX idx_parameter_is_deleted ON parameter(is_deleted);

-- Create indexes for version queries
CREATE INDEX idx_module_create_version ON module(create_version);
CREATE INDEX idx_function_create_version ON function(create_version);
CREATE INDEX idx_parameter_create_version ON parameter(create_version);