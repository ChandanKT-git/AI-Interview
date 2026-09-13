"""Built-in interview content used as a graceful fallback when no Groq key is set.
When GROQ_API_KEY is provided, llm.py uses Groq instead of this bank."""

ROLES = [
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Data Scientist",
    "DevOps Engineer",
    "Product Manager",
    "Mobile Developer",
    "Machine Learning Engineer",
    "HR / Behavioural",
]

ROLE_KEYWORDS = {
    "Backend Developer": ["api", "database", "sql", "index", "cache", "latency", "scal", "microservice", "rest", "queue", "concurrency", "auth", "endpoint", "schema", "transaction"],
    "Frontend Developer": ["component", "state", "render", "react", "css", "dom", "hook", "accessibility", "responsive", "bundle", "performance", "props", "virtual", "layout"],
    "Full Stack Developer": ["api", "database", "frontend", "backend", "deploy", "component", "rest", "auth", "state", "scal", "cache", "schema"],
    "Data Scientist": ["model", "data", "feature", "train", "regression", "classification", "metric", "accuracy", "overfit", "pipeline", "statistic", "distribution", "sample", "bias"],
    "DevOps Engineer": ["ci", "cd", "pipeline", "docker", "kubernetes", "deploy", "monitor", "infrastructure", "terraform", "scal", "container", "rollback", "observability", "cloud"],
    "Product Manager": ["user", "metric", "roadmap", "stakeholder", "priorit", "feature", "kpi", "market", "requirement", "backlog", "outcome", "customer", "value"],
    "Mobile Developer": ["app", "ios", "android", "native", "performance", "battery", "offline", "ui", "lifecycle", "state", "api", "responsive"],
    "Machine Learning Engineer": ["model", "train", "deploy", "feature", "pipeline", "inference", "tensor", "gpu", "latency", "dataset", "metric", "serving", "drift"],
    "HR / Behavioural": ["team", "conflict", "challenge", "leadership", "communicat", "deadline", "feedback", "collaborat", "learn", "goal", "responsib", "ownership"],
}

QUESTION_BANK = {
    "Backend Developer": {
        "easy": [
            "What is the difference between SQL and NoSQL databases, and when would you use each?",
            "Explain what a REST API is and the main HTTP methods you would use.",
            "What is the purpose of an index in a database?",
        ],
        "medium": [
            "How would you design a rate limiter for a public API?",
            "Describe how you would handle database connection pooling in a high-traffic service.",
            "Explain the trade-offs between SQL transactions isolation levels.",
        ],
        "hard": [
            "Design a scalable system to process 1 million events per second. Walk me through your architecture.",
            "How would you ensure data consistency across multiple microservices in a distributed transaction?",
            "Explain how you would debug and resolve a memory leak in a long-running backend service.",
        ],
    },
    "Frontend Developer": {
        "easy": [
            "What is the virtual DOM and why is it useful?",
            "Explain the difference between props and state in React.",
            "How do you make a website responsive across devices?",
        ],
        "medium": [
            "How would you optimize the performance of a React application that renders a large list?",
            "Explain how you manage global state in a complex frontend application.",
            "What strategies do you use to improve web accessibility (a11y)?",
        ],
        "hard": [
            "Design the frontend architecture for a real-time collaborative editor like Google Docs.",
            "How would you reduce the initial bundle size and improve Time To Interactive for a large SPA?",
            "Explain how you would implement optimistic UI updates with proper error rollback.",
        ],
    },
    "Full Stack Developer": {
        "easy": [
            "Walk me through what happens when a user submits a form on a web app, end to end.",
            "What is CORS and why does it matter?",
            "How do you store and verify user passwords securely?",
        ],
        "medium": [
            "How would you design authentication and authorization for a multi-role web app?",
            "Describe how you would implement file uploads with progress for large files.",
            "How do you keep frontend and backend data models in sync as the product evolves?",
        ],
        "hard": [
            "Design an end-to-end architecture for a SaaS app supporting 100k concurrent users.",
            "How would you implement real-time notifications across web and mobile clients?",
            "Explain your approach to zero-downtime deployments for a full stack application.",
        ],
    },
    "Data Scientist": {
        "easy": [
            "Explain the difference between supervised and unsupervised learning.",
            "What is overfitting and how can you prevent it?",
            "What is the difference between mean, median and mode, and when is each useful?",
        ],
        "medium": [
            "How do you handle missing or imbalanced data in a classification problem?",
            "Explain precision, recall and F1 score. When would you optimize for each?",
            "Walk me through your process for feature engineering on a tabular dataset.",
        ],
        "hard": [
            "How would you design an experiment to measure the impact of a new recommendation model?",
            "Explain how you would detect and address model drift in production.",
            "Describe how you would build a churn prediction system end to end.",
        ],
    },
    "DevOps Engineer": {
        "easy": [
            "What is the difference between continuous integration and continuous deployment?",
            "What problem does containerization (Docker) solve?",
            "What is infrastructure as code and why is it valuable?",
        ],
        "medium": [
            "How would you design a CI/CD pipeline for a microservices application?",
            "Explain blue-green vs canary deployments and when you'd choose each.",
            "How do you approach monitoring and alerting for a production system?",
        ],
        "hard": [
            "Design a multi-region, highly available infrastructure on the cloud. Walk me through it.",
            "How would you implement zero-downtime database migrations at scale?",
            "Explain how you would respond to and recover from a production outage.",
        ],
    },
    "Product Manager": {
        "easy": [
            "How do you prioritize features when everything seems important?",
            "What metrics would you track for a new product launch?",
            "How do you gather and validate user requirements?",
        ],
        "medium": [
            "Tell me how you would improve the onboarding experience of an existing product.",
            "How do you balance stakeholder requests against the product roadmap?",
            "Describe how you would decide whether to build, buy, or partner for a feature.",
        ],
        "hard": [
            "How would you design and measure the success of a brand new product line?",
            "Walk me through how you would turn around a product with declining engagement.",
            "How do you make a high-stakes decision with incomplete data and tight deadlines?",
        ],
    },
    "Mobile Developer": {
        "easy": [
            "What are the main differences between native and cross-platform mobile development?",
            "How do you handle different screen sizes and orientations?",
            "Explain the typical lifecycle of a mobile app screen.",
        ],
        "medium": [
            "How would you implement offline support and sync in a mobile app?",
            "What strategies do you use to optimize battery and memory usage?",
            "How do you manage app state across navigation and background/foreground transitions?",
        ],
        "hard": [
            "Design the architecture for a mobile app that works seamlessly offline and online.",
            "How would you debug and fix a hard-to-reproduce crash reported only in production?",
            "Explain how you would build a smooth, 60fps infinite-scroll feed with media.",
        ],
    },
    "Machine Learning Engineer": {
        "easy": [
            "What is the difference between training and inference?",
            "Explain the bias-variance tradeoff.",
            "What is a feature pipeline and why does it matter?",
        ],
        "medium": [
            "How would you deploy a machine learning model as a low-latency API?",
            "Explain how you would monitor a model in production for performance degradation.",
            "How do you decide between batch and real-time inference?",
        ],
        "hard": [
            "Design an end-to-end ML platform for training and serving models at scale.",
            "How would you optimize inference latency for a large model under heavy load?",
            "Explain your approach to A/B testing two models safely in production.",
        ],
    },
    "HR / Behavioural": {
        "easy": [
            "Tell me about yourself and what motivates you professionally.",
            "Describe a time you worked well within a team.",
            "What are your greatest strengths and how do they help you at work?",
        ],
        "medium": [
            "Tell me about a time you faced a conflict with a coworker and how you resolved it.",
            "Describe a situation where you had to meet a tight deadline. What did you do?",
            "Tell me about a time you received critical feedback and how you responded.",
        ],
        "hard": [
            "Describe the most challenging project you've led and how you handled setbacks.",
            "Tell me about a time you had to make an unpopular decision. How did you manage it?",
            "Describe a failure you experienced and what you learned from it.",
        ],
    },
}

RESOURCES = {
    "Backend Developer": ["System Design Primer (GitHub)", "Designing Data-Intensive Applications (book)", "REST API Design Best Practices"],
    "Frontend Developer": ["React Docs - Thinking in React", "web.dev Performance guides", "MDN Accessibility tutorials"],
    "Full Stack Developer": ["The Full Stack Open course", "System Design Primer", "OWASP Auth Cheat Sheet"],
    "Data Scientist": ["StatQuest (YouTube)", "Hands-On ML with Scikit-Learn (book)", "Kaggle Learn courses"],
    "DevOps Engineer": ["The DevOps Handbook", "Kubernetes Up & Running", "Google SRE Book"],
    "Product Manager": ["Inspired by Marty Cagan (book)", "Lenny's Newsletter", "Decode and Conquer (book)"],
    "Mobile Developer": ["Official iOS/Android docs", "Ray Wenderlich tutorials", "Mobile System Design guides"],
    "Machine Learning Engineer": ["Made With ML (MLOps)", "Designing ML Systems (book)", "Full Stack Deep Learning"],
    "HR / Behavioural": ["STAR method guide", "Cracking the Behavioural Interview", "Mock interview practice with peers"],
}


def fallback_question(role: str, difficulty: str, asked: list) -> dict:
    role = role if role in QUESTION_BANK else "HR / Behavioural"
    diff = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    pool = QUESTION_BANK[role][diff]
    asked_texts = {a.get("question") for a in asked}
    for q in pool:
        if q not in asked_texts:
            return {"question": q, "category": "behavioural" if "HR" in role else "technical", "difficulty": diff}
    # all used at this difficulty, try other difficulties
    for d in ("medium", "hard", "easy"):
        for q in QUESTION_BANK[role][d]:
            if q not in asked_texts:
                return {"question": q, "category": "behavioural" if "HR" in role else "technical", "difficulty": d}
    return {"question": pool[0], "category": "technical", "difficulty": diff}


def get_resources(role: str) -> list:
    return RESOURCES.get(role, RESOURCES["HR / Behavioural"])
