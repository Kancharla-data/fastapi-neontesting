# FastAPI PostgreSQL Demo (Clothing Store)

This is a working demo for a FastAPI service with a PostgreSQL database. Features:
- Development environment with DB
- Local real-time development
- Database migration with sample data seed
- Testing using the VSCode Extension REST Client (
humao.rest-client) 

### Making changes to the DB Schema
Edit the file `db/schema.sql`. Add new columns using the extremely practical `ALTER TABLE [table] ADD COLUMN IF NOT EXISTS [column] ...` syntax.

### For local real-time development using docker-compose

Rename `.env-example` to `.env` to override the `MODE=production`set in the `Dockerfile`. Note that this needs a valueless declaration of `MODE` in `docker-compose.yml`

The docker-compose includes a PostgreSQL database and the app will use it by default. You can connect to it locally from outside of docker using localhost as server: `postgresql://devuser:devpassword@localhost:5432/devdb`

To run the container locally:
`docker-compose up --build`

### Cloud Deployment
- In your cloud platform's environment variables, set the DATABASE_URL parameter to your production database
- Note that docker-compose is only for development and will not run in production
