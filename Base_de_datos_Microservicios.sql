CREATE TABLE estado (
    id     INTEGER NOT NULL,
    estado NVARCHAR2(20)
);

ALTER TABLE estado ADD CONSTRAINT estado_pk PRIMARY KEY ( id );

CREATE TABLE ingrediente_receta (
    id              INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL,
    ingredientes_id INTEGER NOT NULL,
    recetas_id      INTEGER NOT NULL
);

ALTER TABLE ingrediente_receta ADD CONSTRAINT ingrediente_receta_pk PRIMARY KEY ( id );

CREATE TABLE ingredientes (
    id          INTEGER NOT NULL,
    ingrediente NVARCHAR2(50),
    inventario  INTEGER NOT NULL
);

ALTER TABLE ingredientes ADD CONSTRAINT ingredientes_pk PRIMARY KEY ( id );

CREATE TABLE orden (
    id         INTEGER AUTO_INCREMENT PRIMARY KEY,
    Actualizacion  TIMESTAMP,
    recetas_id INTEGER NOT NULL,
    estado_id  INTEGER NOT NULL
);


CREATE TABLE recetas (
    id          INTEGER NOT NULL,
    nombre      NVARCHAR2(1),
    descripcion NVARCHAR2(1)
);

ALTER TABLE recetas ADD CONSTRAINT recetas_pk PRIMARY KEY ( id );

ALTER TABLE ingrediente_receta
    ADD CONSTRAINT ingrediente_receta_ingredientes_fk FOREIGN KEY ( ingredientes_id )
        REFERENCES ingredientes ( id );

ALTER TABLE ingrediente_receta
    ADD CONSTRAINT ingrediente_receta_recetas_fk FOREIGN KEY ( recetas_id )
        REFERENCES recetas ( id );

ALTER TABLE orden
    ADD CONSTRAINT orden_estado_fk FOREIGN KEY ( estado_id )
        REFERENCES estado ( id );

ALTER TABLE orden
    ADD CONSTRAINT orden_recetas_fk FOREIGN KEY ( recetas_id )
        REFERENCES recetas ( id );