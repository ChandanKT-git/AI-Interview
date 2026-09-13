"""Curated, ready-to-use interview packs seeded at startup (created_by='system')."""
import uuid
from datetime import datetime, timezone

from db import db

CURATED = [
    {
        "title": "Backend Engineer — Core Screen",
        "role": "Backend Developer", "industry": "Technology", "category": "tech", "difficulty": "medium",
        "description": "API design, databases, scalability and reliability fundamentals.",
        "questions": [
            {"question": "Walk me through how you would design a REST API for a URL shortener.", "category": "technical", "difficulty": "medium"},
            {"question": "When would you choose a SQL database over a NoSQL one, and vice versa?", "category": "technical", "difficulty": "medium"},
            {"question": "How would you design a rate limiter for a public API?", "category": "technical", "difficulty": "medium"},
            {"question": "Explain how you would add caching to reduce database load, and the risks involved.", "category": "technical", "difficulty": "hard"},
            {"question": "How do you ensure data consistency across multiple microservices?", "category": "technical", "difficulty": "hard"},
        ],
    },
    {
        "title": "Frontend Engineer — React Focus",
        "role": "Frontend Developer", "industry": "Technology", "category": "tech", "difficulty": "medium",
        "description": "React, state management, performance and accessibility.",
        "questions": [
            {"question": "Explain the difference between state and props in React with an example.", "category": "technical", "difficulty": "easy"},
            {"question": "How would you optimize a React app that renders a very large list?", "category": "technical", "difficulty": "medium"},
            {"question": "How do you manage global state in a complex frontend application?", "category": "technical", "difficulty": "medium"},
            {"question": "What strategies do you use to improve web accessibility?", "category": "technical", "difficulty": "medium"},
            {"question": "How would you reduce bundle size and improve Time To Interactive for a large SPA?", "category": "technical", "difficulty": "hard"},
        ],
    },
    {
        "title": "Data Scientist — Fundamentals",
        "role": "Data Scientist", "industry": "Technology", "category": "tech", "difficulty": "medium",
        "description": "ML concepts, evaluation metrics and practical modelling.",
        "questions": [
            {"question": "Explain the difference between supervised and unsupervised learning.", "category": "technical", "difficulty": "easy"},
            {"question": "What is overfitting and how do you prevent it?", "category": "technical", "difficulty": "easy"},
            {"question": "How do you handle imbalanced data in a classification problem?", "category": "technical", "difficulty": "medium"},
            {"question": "Explain precision, recall and F1 — when would you optimize for each?", "category": "technical", "difficulty": "medium"},
            {"question": "How would you detect and address model drift in production?", "category": "technical", "difficulty": "hard"},
        ],
    },
    {
        "title": "HR Screening — General",
        "role": "HR / Behavioural", "industry": "Technology", "category": "hr", "difficulty": "easy",
        "description": "Classic HR round: motivation, fit and self-awareness.",
        "questions": [
            {"question": "Tell me about yourself and what motivates you professionally.", "category": "hr", "difficulty": "easy"},
            {"question": "Why do you want to work here, and why this role?", "category": "hr", "difficulty": "easy"},
            {"question": "What are your greatest strengths and one area you're actively improving?", "category": "hr", "difficulty": "easy"},
            {"question": "Where do you see yourself in three to five years?", "category": "hr", "difficulty": "medium"},
            {"question": "What are your salary expectations and what factors matter most to you in an offer?", "category": "hr", "difficulty": "medium"},
        ],
    },
    {
        "title": "Behavioural — Leadership & Conflict",
        "role": "HR / Behavioural", "industry": "Technology", "category": "behavioural", "difficulty": "medium",
        "description": "STAR-style behavioural questions on teamwork, conflict and ownership.",
        "questions": [
            {"question": "Tell me about a time you faced a conflict with a coworker and how you resolved it.", "category": "behavioural", "difficulty": "medium"},
            {"question": "Describe a situation where you had to meet a very tight deadline.", "category": "behavioural", "difficulty": "medium"},
            {"question": "Tell me about a time you received critical feedback and how you responded.", "category": "behavioural", "difficulty": "medium"},
            {"question": "Describe the most challenging project you've led and how you handled setbacks.", "category": "behavioural", "difficulty": "hard"},
            {"question": "Tell me about a failure you experienced and what you learned from it.", "category": "behavioural", "difficulty": "hard"},
        ],
    },
    {
        "title": "DevOps Engineer — CI/CD & Reliability",
        "role": "DevOps Engineer", "industry": "Technology", "category": "tech", "difficulty": "medium",
        "description": "Pipelines, deployments, infrastructure and incident response.",
        "questions": [
            {"question": "What is the difference between continuous integration and continuous deployment?", "category": "technical", "difficulty": "easy"},
            {"question": "How would you design a CI/CD pipeline for a microservices application?", "category": "technical", "difficulty": "medium"},
            {"question": "Explain blue-green vs canary deployments and when you'd choose each.", "category": "technical", "difficulty": "medium"},
            {"question": "How do you approach monitoring and alerting for a production system?", "category": "technical", "difficulty": "medium"},
            {"question": "Walk me through how you would respond to and recover from a production outage.", "category": "technical", "difficulty": "hard"},
        ],
    },
    {
        "title": "Product Manager — Core Round",
        "role": "Product Manager", "industry": "Technology", "category": "behavioural", "difficulty": "medium",
        "description": "Prioritization, metrics and product judgement.",
        "questions": [
            {"question": "How do you prioritize features when everything seems important?", "category": "behavioural", "difficulty": "medium"},
            {"question": "What metrics would you track for a new product launch?", "category": "behavioural", "difficulty": "medium"},
            {"question": "How would you improve the onboarding experience of an existing product?", "category": "behavioural", "difficulty": "medium"},
            {"question": "How do you balance stakeholder requests against the product roadmap?", "category": "behavioural", "difficulty": "hard"},
            {"question": "How would you turn around a product with declining engagement?", "category": "behavioural", "difficulty": "hard"},
        ],
    },
]


async def seed_curated_packs():
    for p in CURATED:
        exists = await db.packs.find_one({"title": p["title"], "is_curated": True})
        if exists:
            continue
        await db.packs.insert_one({
            "pack_id": f"pack_{uuid.uuid4().hex[:12]}",
            "title": p["title"],
            "role": p["role"],
            "industry": p["industry"],
            "category": p["category"],
            "description": p["description"],
            "difficulty": p["difficulty"],
            "questions": p["questions"],
            "is_curated": True,
            "created_by": "system",
            "created_by_name": "InterviewCoach Library",
            "created_at": datetime.now(timezone.utc),
        })
