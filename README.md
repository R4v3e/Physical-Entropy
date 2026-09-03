# Physical Entropy

Physical entropy-based random number generator using a lava lamp, SHA-256, FastAPI, SQLite, and Docker.

## How it works

A camera captures the lava lamp and extracts a region containing the moving wax. The captured image is processed with SHA-256, and part of the resulting hash is used to produce a 32-bit random value. The number and image are stored in a database and can be accessed later, allowing data to be collected when needed instead of requiring the system to be active continuously.

The project also provides a REST API and a web interface for viewing generated samples and comparing their statistical distribution with Python's random number generator.

## API

The project provides a REST API for accessing generated random numbers, sample data, status information and database statistics.

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/rng` | Generate and consume a random number |
| GET | `/api/rng/status` | Check the number of available samples |
| GET | `/api/samples` | List collected samples |
| GET | `/api/samples/{id}` | Get a specific sample |
| GET | `/api/stats` | Get dataset statistics |
| GET | `/api/stats/distribution` | Get data for statistical distribution comparison |
