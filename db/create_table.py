# script

import dotenv

dotenv.load_dotenv("../envs/db.env")

import engine
import models

# Create the tables
models.Base.metadata.create_all(engine.engine, checkfirst=False)
