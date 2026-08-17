# QMMO Notice Board

## Group 3

**Group Tag:** QMMO

### Team Members

-   Omar Haifa
-   Qays
-   Michael
-   Mosley

## Project Overview

QMMO Notice Board is a full-stack web application for posting and
viewing notices in one central location.

The application allows users to create notices, view existing notices,
delete notices, assign a priority level to each notice, and filter
notices based on priority.

The project was implemented independently by Omar Ali as part of the
Group 3 project.

The application uses React for the frontend, FastAPI for the backend,
MongoDB Atlas for the database, and AWS services for deployment.

## USP - Notice Priority and Filtering

The Unique Selling Point (USP) for the QMMO Notice Board is a notice
priority and filtering system.

When creating a notice, the user can select one of three priority
levels:

-   Normal
-   Important
-   Urgent

Each notice displays its priority so that more important announcements
are easier to identify.

The notice board can also be filtered by:

-   All
-   Normal
-   Important
-   Urgent

This makes it easier for users to quickly find notices based on their
importance.

## Features

-   Create a new notice
-   View all notices
-   Delete notices
-   Assign priority levels to notices
-   Filter notices by priority
-   Responsive React user interface
-   REST API built with FastAPI
-   MongoDB database storage
-   AWS cloud deployment

## Technology Stack

### Frontend

-   React
-   JavaScript
-   HTML
-   CSS
-   Vite
-   Axios

### Backend

-   Python
-   FastAPI
-   Pydantic
-   PyMongo
-   Uvicorn

### Database

-   MongoDB
-   MongoDB Atlas

### AWS

-   Amazon EC2
-   Amazon S3
-   Amazon CloudFront
-   Amazon API Gateway

## Application Architecture

The backend follows a layered architecture to separate the different
responsibilities of the application.

``` text
React Frontend
      |
      v
API Gateway
      |
      v
FastAPI Router
      |
      v
Service Layer
      |
      v
Repository Layer
      |
      v
MongoDB Atlas
```

### Router Layer

The router handles incoming HTTP requests and defines the API endpoints.

### Service Layer

The service layer handles the application logic and connects the router
layer to the repository layer.

### Repository Layer

The repository layer handles communication with MongoDB, including
creating, retrieving, and deleting notices.

### Model Layer

Pydantic models define the structure of the notice data sent to and
returned from the API.

## Project Structure

``` text
Group3-Omar_Qays_Michael_Mosley_QMMO/
|
|-- backend/
|   |-- app/
|   |   |-- db/
|   |   |   `-- database.py
|   |   |-- models/
|   |   |   `-- notice.py
|   |   |-- repositories/
|   |   |   `-- notice_repository.py
|   |   |-- routers/
|   |   |   `-- notice_router.py
|   |   |-- services/
|   |   |   `-- notice_service.py
|   |   `-- main.py
|   `-- requirements.txt
|
|-- frontend/
|   |-- src/
|   |   |-- api/
|   |   |   `-- api.js
|   |   |-- App.jsx
|   |   |-- App.css
|   |   |-- index.css
|   |   `-- main.jsx
|   |-- package.json
|   `-- vite.config.js
|
|-- ASSIGNMENT.md
`-- README.md
```

## API Endpoints

### Get All Notices

``` http
GET /notices
```

Returns all notices currently stored in MongoDB.

### Create Notice

``` http
POST /notices
```

Example request:

``` json
{
  "name": "Omar",
  "message": "Team meeting at 4 PM",
  "priority": "Urgent"
}
```

### Delete Notice

``` http
DELETE /notices/{notice_id}
```

Deletes a notice using its MongoDB ID.

## Running the Project Locally

### Backend

Go to the backend directory:

``` bash
cd backend
```

Create a virtual environment:

``` bash
python -m venv venv
```

Activate the virtual environment on Windows:

``` bash
venv\Scripts\activate
```

Install the backend dependencies:

``` bash
pip install -r requirements.txt
```

Create a `.env` file containing the MongoDB connection information:

``` env
MONGODB_URL=your_mongodb_connection_string
```

Database credentials should not be committed to GitHub.

Start the FastAPI backend:

``` bash
python -m uvicorn app.main:app --reload
```

Swagger UI is available locally at:

``` text
http://127.0.0.1:8000/docs
```

### Frontend

Go to the frontend directory:

``` bash
cd frontend
```

Install the frontend dependencies:

``` bash
npm install
```

Start the React development server:

``` bash
npm run dev
```

## AWS Deployment

The application is deployed using multiple AWS services.

### Frontend Deployment

``` text
React
  |
  v
Amazon S3
  |
  v
Amazon CloudFront
```

The React application is built using Vite. The production build files
are stored in an Amazon S3 bucket, and CloudFront provides the public
HTTPS frontend.

### Backend Deployment

``` text
Amazon API Gateway
        |
        v
Amazon EC2
        |
        v
FastAPI
        |
        v
MongoDB Atlas
```

FastAPI runs on an Amazon EC2 instance. API Gateway provides an HTTPS
endpoint and forwards API requests to the FastAPI application running on
EC2.

MongoDB Atlas provides the cloud-hosted MongoDB database.

## Deployed Application

### Frontend

https://d1qrvfuf1egg8d.cloudfront.net

### Backend Swagger UI

https://d1a13cxnr8.execute-api.us-east-1.amazonaws.com/docs

## Security

Sensitive MongoDB credentials are stored using environment variables
instead of being included directly in the source code.

The `.env` file is excluded from Git so database credentials are not
pushed to the repository.

MongoDB Atlas uses an IP access list to control database connections.

The Amazon S3 frontend bucket is kept private and accessed through
CloudFront.

FastAPI CORS settings allow the deployed CloudFront frontend to
communicate with the backend API.

## Development and Git Workflow

The application implementation was completed independently by Omar Ali
within a fork of the BeCloudReady workshops repository.

The project was developed and tested locally before the frontend and
backend were deployed to AWS. Changes were committed and pushed to the
`master` branch of the fork throughout development.

After final testing and documentation are complete, the project is
submitted through a pull request from the fork's `master` branch to the
upstream BeCloudReady workshops repository.
