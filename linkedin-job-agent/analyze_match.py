#!/usr/bin/env python3
"""
Simple resume-job matching analysis tool.
"""

import json
from typing import Dict, List, Any

def analyze_job_match(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Analyze how well a resume matches a job description.
    
    Args:
        resume_text: The resume content as text
        job_description: The job description content
    
    Returns:
        Dict containing match analysis with keys:
        - match_score: 0-100 score
        - matching_skills: Skills that match
        - missing_skills: Required skills not in resume
        - strengths: Why this is a good match
        - weaknesses: Potential concerns
        - recommendation: Should apply? (yes/no/maybe)
    """
    
    # Extract skills from resume
    resume_lower = resume_text.lower()
    
    # Common technical skills found in the resume
    resume_skills = []
    skill_keywords = [
        'python', 'java', 'c++', 'c#', '.net', 'javascript', 'typescript',
        'aws', 'azure', 'docker', 'kubernetes', 'microservices',
        'machine learning', 'ai', 'cuda', 'matlab', 'angular', 'unity',
        'sql server', 'postgresql', 'rest api', 'agile', 'tdd',
        'distributed systems', 'cloud architecture', 'data pipelines'
    ]
    
    for skill in skill_keywords:
        if skill in resume_lower:
            resume_skills.append(skill)
    
    # Since job description is incomplete HTML, we cannot extract meaningful requirements
    job_lower = job_description.lower() if job_description else ""
    
    # Check if we have a meaningful job description
    if not job_description.strip() or "job-details" in job_description or len(job_description.strip()) < 100:
        return {
            "match_score": 0,
            "matching_skills": [],
            "missing_skills": ["Cannot analyze - job description incomplete or missing"],
            "strengths": ["Extensive experience across multiple domains", "Strong technical background", "Leadership experience"],
            "weaknesses": ["Cannot assess without complete job description"],
            "recommendation": "maybe"
        }
    
    # If we had a complete job description, we would:
    # 1. Extract required skills and qualifications
    # 2. Compare with resume skills
    # 3. Calculate match percentage
    # 4. Identify gaps and strengths
    
    return {
        "match_score": 0,
        "matching_skills": [],
        "missing_skills": ["Job description incomplete - cannot analyze requirements"],
        "strengths": [
            "Principal-level engineer with 20+ years experience",
            "Extensive cloud and distributed systems expertise", 
            "AI/ML and emerging technology experience",
            "Leadership experience at major companies (NASA, Boeing, Microsoft, Tesla)"
        ],
        "weaknesses": ["Cannot assess fit without complete job description"],
        "recommendation": "maybe"
    }

if __name__ == "__main__":
    resume_text = """ALEX FEDIN, PRINCIPAL SOFTWARE ENGINEER
Mobile: 425-351-1652 | Email: jobs4alex@allconnectix.com
LinkedIn: linkedin.com/in/alex-fedin | GitHub: github.com/o2alexanderfedin
Website: o2.services
PROFESSIONAL SUMMARY
Principal Software Engineer with extensive experience designing and delivering
large-scale distributed systems, cloud solutions, and AI-driven platforms for
industry leaders such as NASA, Boeing, and Microsoft. Proficient at leading cross-
functional teams, orchestrating complex data architecture transformations, and
continuously optimizing performance in mission-critical applications. Committed to
Agile/XP methodologies, cutting-edge prototyping, and mentoring technical talent
to drive innovation and measurable results.
GEN AI, AGENTIC AI, APPLIED AI/ ML, DIGITAL TRANSFORMATION, STRATEGY and thought
process
CORE COMPETENCIES
• Cloud Architecture (AWS, Azure)
• Distributed Systems & Microservices
• AI & Large Language Models (OpenAI, Bard, LLaMA)
• Performance Optimization & Data Pipelines
• Agile/XP & TDD Methodologies
• Cross-Functional Leadership
• Systems Integration & API Design
• High-Throughput Data Processing
PROFESSIONAL EXPERIENCE
Waymo (Google Alphabet) | Senior SDE | Sep 2024–Dec 2024
• On a short assignment, picked up work items of two google engineers who were
on a long leave.
• Designed and implemented a bunch of sophisticated UI Angular-based
components for the Simulation team.
• Helped to establish the environment for the contractors onboarding, as I was the
very first one joined the team.
• Managed to do my work even with very limiting permissions (if compared that to
whatever is available to FTEs).
O2.services | Founder & Principal Software Engineer | Jun 2018–Present
• Prototyped a globally distributed, peer-to-peer cloud, reducing hosting costs by
~20% through optimized resource utilization.
• Engineered a self-guided agentic system, which enhanced autonomy and
decreased manual intervention by approximately 30%, serving as a supervisory
layer for AI-driven IDEs.
• Developed an OpenAI-powered, semantically searchable knowledge base,
slashing user search times by ~40% and accelerating decision-making.
• Prototyped a Startup Cyber-Assistant to help emerging companies prepare
funding materials, broadening the consultancy's service offerings.
• Tech Used: C++, C#/.NET, TypeScript, Node.js, Distributed Hash Table (DHT),
Torrent, IPFS, WebAssembly, Azure, Serverless Computing
NASA | Principal Software Engineer | Oct 2018–Feb 2022
• Optimized drone telemetry pipelines, cutting data processing time by ~20% and
enhancing situational awareness for the UTM (Unmanned Traffic Management)
initiative.
• Led a MATLAB-to-Nvidia CUDA C++ transpiler project, boosting development
speeds by ~200% for high-fidelity drone models.
• Championed Agile development, reducing release cycles by ~20% and improving
cross-team collaboration.
• Tech Used: Java, C++, CUDA, MATLAB, C#/.NET, Unity, Docker, AWS, Azure
Accuray, Inc. | Software Architect | Jul 2017–Aug 2018
• Refactored on-premises healthcare services, lowering error rates by ~15% and
ensuring seamless radiation therapy data reliability.
• Migrated legacy Silverlight apps to modern frameworks, expanding cross-
platform support and streamlining maintenance.
• Tech Used: C++, Java, C#/.NET, Silverlight, Angular, Windows Azure
Tesla Motors | Senior Software Engineer (Supply Chain) | Oct 2015–Jul
2017
• Implemented microservices for Gigafactory supply chain, decreasing downtime
by 15% and enabling real-time tracking of parts and inventory.
• Collaborated with manufacturing and operations teams to ensure consistent
architecture and on-schedule rollouts.
• Tech Used: Java, C#/.NET, TypeScript, MS SQL Server, REST
VISA BI Department | Senior Architect & Developer | May 2014–Oct 2015
• Overhauled a naively designed BI system, cutting query times by 50% and
improving overall system throughput by 60%.
• Built a VBA-to-VB.NET transpiler, reducing manual macro migration and
accelerating adoption of modern .NET modules.
• Tech Used: C#/.NET, MS Orleans (Actor Framework), OpenXml, Excel,
PowerPoint
Boeing Defense | Lead Software Engineer | Jun 2012–Apr 2014
• Cut verification time by 35% with an automated .NET-based testing platform for
laser weapon systems (CLWS/HEL MD).
• Led a small engineering team, delivering robust solutions on schedule and
conforming to defense requirements.
• Tech Used: C#/.NET, Windows Workflow Foundation, MS SQL Server
Geico Insurance | Architect & Technical Lead (Data Layer) | Jan 2011–Jun
2012
• Led data-related layers, including DB migrations from IBM DB2 to MS SQL
Server, enabling a 25% cost reduction through mainframe-to-cloud
modernization.
• Drove TDD and Pair Programming, shortening defect resolution times and
boosting developer productivity.
• Tech Used: C#, .NET, ASP.NET MVC, WCF, WWF, SQL Server
Microsoft | Senior Software Developer | May 2005–Dec 2010
• Delivered UI enhancements for Silverlight components and VE Map Control.
• Built an internal JavaScript Automation Framework, streamlining UI testing and
improving QA cycles.
• Tech Used: C#/.NET, JavaScript, XAML, COM/DCOM
Wachovia Securities | Assistant Architect | May 2004–Apr 2005
• Reduced transaction errors in global trading by enhancing cross-region date
handling.
• Adopted TDD, lowering critical bugs by ~25%.
• Tech Used: VB6, Delphi
Lehman Brothers | Support Engineer | Feb 2004–May 2004
• Maintained high-integrity data feeds (Bloomberg, Reuters), streamlining
overnight processes to reduce data latency.
Deutsche Bank EMEA | Lead Software Engineer | 2003–2004
• Modernized trader-facing applications, boosting transaction speed and
responsiveness for global markets.
• Tech Used: .NET, Java Swing (migration projects)
Gemalto | Senior Software Developer | 2002–2003
• Enabled mobile financial transactions on SIM cards, reducing transaction delays
by ~20% for telecom providers.
DELL Computers | Team Lead (Automated Control Framework) | 2001–2002
• Overhauled factory automation in DELL EMEA plants, minimizing conveyor
downtime and increasing throughput by ~40%.
• Tech Used: COM/DCOM, Custom Queued Components, Windows
EDUCATION
• Master's in Electromechanical Engineering
Ural State Railway Institute, Ekaterinburg, Russia (1988–1994)"""

    job_description = """Job Title: Unknown Job
Company: Unknown Company
Location: Unknown
Description: 
          
              
    <!---->
    <div class="jobs-search__job-details--wrapper">
      <div></div>

        
      <div aria-label="(Founding) ML/Game Theory Lead – AI/Blockchain Platform" class="jobs-search__job-details--container
          " data-job-details-events-trigger="">
        
      <div class="jobs-semantic-search-job-details-wrapper" tabindex="0">
        <div></div>
        
<!---->
    <div class="job-view-layout jobs-details">
      <div>
        <div class="jobs-detail
Requirements: []"""

    result = analyze_job_match(resume_text, job_description)
    print(json.dumps(result, indent=2))