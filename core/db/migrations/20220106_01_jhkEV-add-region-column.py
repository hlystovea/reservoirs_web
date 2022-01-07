"""
Add cascade column
"""

from yoyo import step

__depends__ = {'20211229_01_8I8uE-initial'}

steps = [
    step(
        '''
        CREATE TABLE IF NOT EXISTS regions (
            id serial PRIMARY KEY,
            name varchar(64) NOT NULL,
            slug varchar(64) NOT NULL
        );
        ''',
        '''
        DROP TABLE regions;
        '''
    ),
    step(
        '''
        ALTER TABLE reservoirs
        ADD region_id INT;
        ''',
        '''
        ALTER TABLE reservoirs
        DROP COLUMN region_id;
        '''
    ),
    step(
        '''
        ALTER TABLE reservoirs
        ADD CONSTRAINT fk_region_reservoirs
        FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE SET NULL;
        ''',
        '''
        ALTER TABLE reservoirs
        DROP CONSTRAINT fk_region_reservoirs;
        '''
    )
]
