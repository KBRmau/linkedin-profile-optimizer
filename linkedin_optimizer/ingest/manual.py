from __future__ import annotations

from pathlib import Path

import yaml

from ..models import Education, Experience, Profile, SSI, Target


def profile_to_dict(profile: Profile) -> dict:
    return {
        "name": profile.name,
        "headline": profile.headline,
        "about": profile.about,
        "current_title": profile.current_title,
        "location": profile.location,
        "experiences": [
            {
                "title": e.title,
                "company": e.company,
                "start": e.start,
                "end": e.end,
                "description": e.description,
                "bullets": list(e.bullets),
                "skills": list(e.skills),
            }
            for e in profile.experiences
        ],
        "education": [
            {
                "school": ed.school,
                "degree": ed.degree,
                "field_of_study": ed.field_of_study,
                "start": ed.start,
                "end": ed.end,
            }
            for ed in profile.education
        ],
        "skills": list(profile.skills),
        "certifications": list(profile.certifications),
        "languages": list(profile.languages),
        "featured": list(profile.featured),
        "recent_posts": list(profile.recent_posts),
        "ssi": {
            "professional_brand": profile.ssi.professional_brand,
            "find_people": profile.ssi.find_people,
            "engage_insights": profile.ssi.engage_insights,
            "build_relationships": profile.ssi.build_relationships,
        },
        "target": {
            "role": profile.target.role,
            "audience": profile.target.audience,
            "market": profile.target.market,
            "seniority": profile.target.seniority,
            "language": profile.target.language,
            "tone": profile.target.tone,
            "keywords": list(profile.target.keywords),
            "job_descriptions": list(profile.target.job_descriptions),
        },
    }


def _dict_to_profile(data: dict) -> Profile:
    data = data or {}
    experiences = [
        Experience(
            title=e.get("title", ""),
            company=e.get("company", ""),
            start=e.get("start", ""),
            end=e.get("end", ""),
            description=e.get("description", ""),
            bullets=list(e.get("bullets", []) or []),
            skills=list(e.get("skills", []) or []),
        )
        for e in (data.get("experiences") or [])
    ]
    education = [
        Education(
            school=ed.get("school", ""),
            degree=ed.get("degree", ""),
            field_of_study=ed.get("field_of_study", ""),
            start=ed.get("start", ""),
            end=ed.get("end", ""),
        )
        for ed in (data.get("education") or [])
    ]
    ssi_data = data.get("ssi") or {}
    ssi = SSI(
        professional_brand=ssi_data.get("professional_brand"),
        find_people=ssi_data.get("find_people"),
        engage_insights=ssi_data.get("engage_insights"),
        build_relationships=ssi_data.get("build_relationships"),
    )
    target_data = data.get("target") or {}
    target = Target(
        role=target_data.get("role", ""),
        audience=target_data.get("audience", ""),
        market=target_data.get("market", ""),
        seniority=target_data.get("seniority", ""),
        language=target_data.get("language", ""),
        tone=target_data.get("tone", ""),
        keywords=list(target_data.get("keywords", []) or []),
        job_descriptions=list(target_data.get("job_descriptions", []) or []),
    )
    return Profile(
        name=data.get("name", ""),
        headline=data.get("headline", ""),
        about=data.get("about", ""),
        current_title=data.get("current_title", ""),
        location=data.get("location", ""),
        experiences=experiences,
        education=education,
        skills=list(data.get("skills", []) or []),
        certifications=list(data.get("certifications", []) or []),
        languages=list(data.get("languages", []) or []),
        featured=list(data.get("featured", []) or []),
        recent_posts=list(data.get("recent_posts", []) or []),
        ssi=ssi,
        target=target,
    )


def load_profile_yaml(path: str | Path) -> Profile:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return _dict_to_profile(data)


def save_profile_yaml(profile: Profile, path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(
            profile_to_dict(profile),
            fh,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
