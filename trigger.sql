CREATE OR REPLACE FUNCTION InPhotoGallery()
RETURNS TRIGGER AS $$
BEGIN	
	INSERT INTO product_galleryproduct(photos,product_id)
	VALUES(new.photo,new.id);
	RETURN NEW;
END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER after_insert_product BEFORE INSERT
on product_product 
FOR EACH ROW EXECUTE FUNCTION InPhotoGallery();
