"""Presets for developer-focused LinkedIn positioning."""

DEV_ROLES: dict[str, dict] = {
    "backend-engineer": {
        "label": "Backend Engineer",
        "role": "Backend Engineer",
        "keywords": ["python", "java", "golang", "api", "microservices", "postgresql", "aws"],
        "headline_areas": "APIs, Microservices & Distributed Systems",
        "headline_tech": "Python · Java · Go · PostgreSQL · AWS · Kubernetes",
    },
    "frontend-engineer": {
        "label": "Frontend Engineer",
        "role": "Frontend Engineer",
        "keywords": ["react", "typescript", "javascript", "nextjs", "css", "performance"],
        "headline_areas": "Web Apps, UX Performance & Design Systems",
        "headline_tech": "React · TypeScript · Next.js · JavaScript · CSS · Performance",
    },
    "fullstack-engineer": {
        "label": "Full Stack Engineer",
        "role": "Full Stack Engineer",
        "keywords": ["react", "node", "typescript", "postgresql", "api", "aws"],
        "headline_areas": "Product Engineering, APIs & Full Stack Delivery",
        "headline_tech": "React · Node.js · TypeScript · PostgreSQL · AWS · REST APIs",
    },
    "data-engineer": {
        "label": "Data Engineer",
        "role": "Data Engineer",
        "keywords": ["python", "sql", "spark", "airflow", "dbt", "lakehouse", "iceberg"],
        "headline_areas": "Data Platform, CDP & Reliability",
        "headline_tech": "GCP · Airflow · BigQuery · Spark · Terraform · dbt",
    },
    "devops-engineer": {
        "label": "DevOps / SRE",
        "role": "DevOps Engineer",
        "keywords": ["kubernetes", "terraform", "aws", "ci/cd", "docker", "observability"],
        "headline_areas": "Cloud Infrastructure, Reliability & Platform Ops",
        "headline_tech": "Kubernetes · Terraform · AWS · Docker · CI/CD · Observability",
    },
    "mobile-engineer": {
        "label": "Mobile Engineer",
        "role": "Mobile Engineer",
        "keywords": ["kotlin", "swift", "flutter", "react native", "ios", "android"],
        "headline_areas": "Mobile Apps, Performance & Cross-Platform",
        "headline_tech": "Kotlin · Swift · Flutter · React Native · iOS · Android",
    },
    "staff-engineer": {
        "label": "Staff / Principal Engineer",
        "role": "Staff Software Engineer",
        "keywords": ["architecture", "scalability", "mentoring", "system design", "platform"],
        "headline_areas": "Platform Architecture, Scale & Technical Leadership",
        "headline_tech": "System Design · Distributed Systems · Cloud · Mentoring · Platform",
    },
}

DEFAULT_TARGET = {
    "audience": "recruiters",
    "tone": "technical",
}
