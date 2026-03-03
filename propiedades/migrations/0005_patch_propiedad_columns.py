from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('propiedades', '0004_propiedad_banos_propiedad_descripcion_and_more'),
        ('usuarios', '0005_alter_cliente_id_alter_propietario_id_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Add missing descriptive fields if they are not present
            ALTER TABLE propiedades_propiedad
                ADD COLUMN IF NOT EXISTS descripcion text;

            ALTER TABLE propiedades_propiedad
                ADD COLUMN IF NOT EXISTS direccion varchar(255);

            ALTER TABLE propiedades_propiedad
                ADD COLUMN IF NOT EXISTS habitaciones integer NOT NULL DEFAULT 1;

            ALTER TABLE propiedades_propiedad
                ADD COLUMN IF NOT EXISTS banos integer NOT NULL DEFAULT 1;

            ALTER TABLE propiedades_propiedad
                ADD COLUMN IF NOT EXISTS metros_cuadrados integer;

            ALTER TABLE propiedades_propiedad
                ADD COLUMN IF NOT EXISTS imagen_url varchar(200);

            ALTER TABLE propiedades_propiedad
                ADD COLUMN IF NOT EXISTS propietario_id integer;

            -- Add FK constraint if column exists and constraint is missing
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'propiedades_propiedad' AND column_name = 'propietario_id'
                ) THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints tc
                        JOIN information_schema.constraint_column_usage ccu
                          ON tc.constraint_name = ccu.constraint_name
                        WHERE tc.table_name = 'propiedades_propiedad'
                          AND tc.constraint_type = 'FOREIGN KEY'
                          AND ccu.column_name = 'propietario_id'
                    ) THEN
                        ALTER TABLE propiedades_propiedad
                        ADD CONSTRAINT propiedades_propiedad_propietario_id_fk
                        FOREIGN KEY (propietario_id) REFERENCES usuarios_propietario(id)
                        ON DELETE CASCADE;
                    END IF;
                END IF;
            END$$;
            """,
            reverse_sql="""
            -- No-op rollback to avoid dropping data
            SELECT 1;
            """,
        ),
    ]