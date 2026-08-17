-- Scale indexes for \~1500 companies (marketplace, inquiries, multi-tenant lists)
CREATE INDEX IF NOT EXISTS ix_listings_status ON listings (status);
CREATE INDEX IF NOT EXISTS ix_listings_company_id ON listings (company_id);
CREATE INDEX IF NOT EXISTS ix_listings_material_type ON listings (material_type);
CREATE INDEX IF NOT EXISTS ix_listings_location ON listings (location);
CREATE INDEX IF NOT EXISTS ix_listings_created_at ON listings (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_listings_status_material ON listings (status, material_type);
CREATE INDEX IF NOT EXISTS ix_listings_status_company ON listings (status, company_id);
CREATE INDEX IF NOT EXISTS ix_inquiries_listing_id ON inquiries (listing_id);
CREATE INDEX IF NOT EXISTS ix_inquiries_company_id ON inquiries (company_id);
CREATE INDEX IF NOT EXISTS ix_inquiries_status ON inquiries (status);
CREATE INDEX IF NOT EXISTS ix_inquiries_created_at ON inquiries (created_at DESC);
CREATE INDEX IF NOT EXISTS ix_inquiries_company_status ON inquiries (company_id, status);
CREATE INDEX IF NOT EXISTS ix_documents_company_id ON documents (company_id);
CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id);
CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at DESC);
