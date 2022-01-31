"""
Initial
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
        '''
        CREATE TABLE IF NOT EXISTS reservoirs (
            id serial PRIMARY KEY,
            name varchar(64) NOT NULL,
            slug varchar(64) NOT NULL,
            force_level float,
            normal_level float,
            dead_level float,
            UNIQUE(slug)
        );
        ''',
        '''
        DROP TABLE reservoirs;
        '''
    ),
    step(
        '''
        CREATE TABLE IF NOT EXISTS water_situation (
            id serial PRIMARY KEY,
            date DATE NOT NULL,
            level float NOT NULL,
            free_capacity float,
            inflow float,
            outflow float,
            spillway float,
            reservoir_id INT NOT NULL REFERENCES reservoirs(id) ON DELETE CASCADE,
            UNIQUE(date, reservoir_id)
        );
        ''',
        '''
        DROP TABLE water_situation;
        '''
    )
]
