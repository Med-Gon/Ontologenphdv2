
# OntologyGen

Generate clean, structured OWL ontologies from your MongoDB database in just a few clicks.

![OntologyGen Logo Placeholder](https://github.com/Med-Gon/OntologyGen-phd/assets/ontologygen_logo.png)

**OntologyGen** is a web-based software tool built with Python and Django, designed for the automated generation of OWL ontologies from MongoDB databases using **Formal Concept Analysis (FCA)**. It provides a seamless workflow for extracting structured knowledge from NoSQL databases, simplifying ontology engineering through an interactive web interface.

---

## Table of Contents

- [Software Architecture](#software-architecture)
- [Docker Image](#docker-image)
- [Backend (Django)](#backend-django)
- [Frontend](#frontend)
- [Getting Started](#getting-started)
- [Video Demonstration](#video-demonstration)
- [Utilization](#utilization)
- [Contributing](#contributing)
- [License](#license)

---

## Software Architecture

![Architecture Diagram Placeholder](https://github.com/Med-Gon/OntologyGen-phd/assets/architecture_diagram.png)

The OntologyGen application is structured as a **Django-based web app** with a clean separation between the **backend** (handling FCA, data processing, and ontology generation) and the **frontend** (managing user interactions and data visualization). It uses **MongoDB** as the primary data source and integrates FCA algorithms for concept lattice generation.

### Key Components

1. **MongoDB Integration:** Data source for ontology generation.
2. **Django Backend:** Handles context extraction, lattice generation, and OWL mapping.
3. **Interactive Frontend:** User-friendly web interface for data import, lattice visualization, and ontology export.
4. **Docker Containerization:** Simplifies deployment and setup.

---

## Docker Image

The Docker setup for OntologyGen includes both the backend (Django server) and the MongoDB database for easy local deployment.

### Docker Compose Configuration

```yaml
version: '3'
services:
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - ./data/db:/data/db

  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=ontologygen.settings
    depends_on:
      - mongodb
```

To start the Docker environment, run:

```bash
docker-compose up --build
```

---

## Backend (Django)

### Technologies Used

- **Python 3.11+**
- **Django 4.2+**
- **PyMongo**
- **Docker**

### Key Features

- Automated context extraction from MongoDB collections.
- Concept lattice generation using FCA.
- Ontology class and property mapping.
- OWL file export.

---

## Frontend

### Technologies Used

- **HTML/CSS**
- **JavaScript**
- **Bootstrap (for responsive design)**

### Frontend Project Structure

The frontend is built using Django templates for seamless integration with the backend logic.

- **Templates:** HTML pages for each step in the ontology generation process.
- **Static Files:** CSS for styling and JavaScript for dynamic interactions.
- **User Interface:** Clean, minimal design with step-by-step navigation.

---

## Getting Started

### Prerequisites

1. **Git:**  
   - Make sure you have Git installed. If not, download and install it from [git-scm.com](https://git-scm.com/).

2. **Docker:**  
   - Make sure you have Docker installed. If not, download and install it from [docker.com](https://www.docker.com/).

### Steps

1. **Clone the Repository:**

```bash
git clone https://github.com/Med-Gon/OntologyGen-phd.git
cd OntologyGen-phd
```

2. **Build and Run Docker Containers:**

```bash
docker-compose up --build
```

3. **Access the Application:**

Open your browser and navigate to:

```
http://localhost:8000
```

---

## Video Demonstration

Click the link below to watch a demonstration video:

**Video Link Placeholder** *(Coming Soon)*

---

## Utilization

### Steps to Use OntologyGen

1. **Connect to MongoDB:**  
   Enter your MongoDB connection string or upload a JSON dump file to import data.  
   *Placeholder for connection screen screenshot.*

2. **Generate Formal Context:**  
   Review the automatically generated formal context table.  
   *Placeholder for context table screenshot.*

3. **Create Concept Lattice:**  
   Visualize the relationships between collections and attributes.  
   *Placeholder for concept lattice screenshot.*

4. **Apply Mapping Rules:**  
   Convert the lattice to an OWL ontology structure.  
   *Placeholder for mapping rules screenshot.*

5. **Export Ontology:**  
   Download the generated OWL file for further use.  
   *Placeholder for OWL export screenshot.*

---

## Contributing

We welcome contributions from the community! If you’d like to contribute to **OntologyGen**, please fork the repository and submit a pull request.

### Contributors

- Elmehdi Elguerraoui ([GitHub](https://github.com/Med-Gon))
- Boutkhoum Omar ([GitHub](https://github.com/username))
- Hanine Mohamed ([GitHub](https://github.com/username))

---

## License

This project is licensed under the **MIT License**. You are free to use, modify, and distribute this software as long as the original license terms are respected.

See the [`LICENSE`](LICENSE) file for details.

---
